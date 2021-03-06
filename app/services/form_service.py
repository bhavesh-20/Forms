from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.sql.expression import delete, insert, select, update

from app import db, spreadsheet_service
from app.models import Form
from app.schemas import FormMetadata, UserResponse


class FormService:
    @classmethod
    def create_spreadsheet(cls, form_id: str, title: str, user_email: str):
        spreadsheet = spreadsheet_service.create(str(form_id))
        spreadsheet.share(user_email, perm_type="user", role="writer")
        worksheet = spreadsheet.get_worksheet(0)
        worksheet.update_title(title)
        worksheet.resize(rows=1, cols=15)
        worksheet.update_cell(1, 1, "Mobile Number")
        worksheet.format(
            "A1:A1",
            {
                "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                "horizontalAlignment": "CENTER",
                "textFormat": {
                    "foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0},
                    "fontSize": 12,
                    "bold": True,
                },
            },
        )
        worksheet.columns_auto_resize(0, 15)

    @classmethod
    async def create_form(
        cls,
        form_metadata: FormMetadata,
        user: UserResponse,
        background_tasks: BackgroundTasks,
    ):
        form = await db.execute(
            insert(Form).values(
                owner_id=user.id,
                title=form_metadata.title,
                description=form_metadata.description,
            )
        )
        background_tasks.add_task(
            cls.create_spreadsheet, form, form_metadata.title, user.email
        )
        return {"message": "Form created successfully", "form_id": form}

    @classmethod
    async def get_user_form(cls, form_id: str, user: UserResponse):
        form = await db.fetch_one(
            select([Form]).where(Form.id == form_id, Form.owner_id == user.id)
        )
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
        return form

    @classmethod
    async def get_form(cls, form_id: str):
        form = await db.fetch_one(select([Form]).where(Form.id == form_id))
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
        return form

    @classmethod
    def update_spreadsheet(cls, form_id: str, title: str):
        spreadsheet = spreadsheet_service.open(form_id)
        worksheet = spreadsheet.get_worksheet(0)
        worksheet.update_title(title)

    @classmethod
    async def update_form(
        cls,
        form_id: str,
        form_metadata: FormMetadata,
        user: UserResponse,
        background_tasks: BackgroundTasks,
    ):
        form = await cls.get_user_form(form_id, user)
        await db.execute(
            update(Form)
            .where(Form.id == form_id)
            .values(title=form_metadata.title, description=form_metadata.description)
        )
        background_tasks.add_task(cls.update_spreadsheet, form_id, form_metadata.title)
        return await cls.get_form(form_id)

    @classmethod
    def delete_spreadsheet(cls, form_id: str):
        spreadsheet_service.del_spreadsheet(spreadsheet_service.open(str(form_id)).id)

    @classmethod
    async def delete_form(
        cls, form_id: str, user: UserResponse, background_tasks: BackgroundTasks
    ):
        form = await cls.get_user_form(form_id, user)
        await db.execute(delete(Form).where(Form.id == form_id))
        background_tasks.add_task(cls.delete_spreadsheet, form_id)
        return {"message": "Form deleted successfully"}
