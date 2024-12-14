from aiogram.fsm.state import State, StatesGroup

class AddContactState(StatesGroup):
    waiting_for_code = State()
    waiting_for_contact_info = State()

class DeleteContactState(StatesGroup):
    waiting_for_code = State()

class EnterCodeState(StatesGroup):
    waiting_for_code = State()

class GetImageState(StatesGroup):
    waiting_for_code = State()

class ModerationStates(StatesGroup):
    waiting_for_user_id = State()