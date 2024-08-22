from RPA.Robocorp.WorkItems import WorkItems

class EnvConfig:
    def __init__(self) -> None:
        work_items = WorkItems()
        work_items.get_input_work_item()
        self.env_vars = work_items.get_work_item_variables()
        print(self.env_vars)

    def get_keyword(self):
        return self.env_vars["KEYWORD"]
    
    def get_months(self):
        return self.env_vars["MONTHS"]