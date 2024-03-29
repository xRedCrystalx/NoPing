import sys, json, typing, os
sys.dont_write_bytecode = True
import src.connector as con

class Database:
    def __init__(self) -> None:
        self.shared: con.Shared = con.shared

    def load_data(self, id: int | None = None, db: str = None) -> dict[str, typing.Any]:
        if id:
            try:
                with open(f"{self.shared.path}/databases/{"users" if db == "USERS" else "servers"}/{id}.json") as file:
                    return json.load(file)
            except Exception as error:
                self.shared.logger.log(f"@databaseHandler.load_data: Error trying to load data for {id}. {type(error).__name__}: {error}", "ERROR")
        else:
            try:
                with open(f"{self.shared.path}/src/config.json") as file:
                    return json.load(file)
            except Exception as error:
                self.shared.logger.log(f"@databaseHandler.load_data: Error trying to load bot's config. {type(error).__name__}: {error}", "ERROR")

    def save_data(self, id: int, update_data: dict, db: str = None) -> None:
        with open(f"{self.shared.path}/database/{"users" if db == "USERS" else "servers"}/{id}.json", "w") as old_data:
            try:
                json.dump(update_data, old_data, indent=4)
            except Exception as error:
                self.shared.logger.log(f"@databaseHandler.save_data: Error trying to save data for {id}. {type(error).__name__}: {error}", "ERROR")

    # possible update needed
    def add_value(self, key: str, value_type: typing.Literal["str", "int", "bool", "list", "dict", "none"], path: str | None = None, db_id: int | None = None) -> bool:
        values: dict[str, typing.Any] = {
            "str" : "",
            "int" : 0,
            "bool" : False,
            "list" : [],
            "dict" : {},
            "none" : None
        }

        def recursive_add_value(d, path_segments):
            if not path_segments:
                # We've reached the target level, so add the key-value pair
                d[key] = values.get(value_type)
            else:
                # Continue navigating the path
                current_segment = path_segments[0]
                if current_segment == '*':
                    for k, v in d.items():
                        if isinstance(v, dict):
                            recursive_add_value(v, path_segments[1:])
                        elif isinstance(v, list):
                            for item in v:
                                recursive_add_value(item, path_segments[1:])
                elif current_segment in d:
                    recursive_add_value(d[current_segment], path_segments[1:])

        if not db_id:
            for file in os.listdir(f"{self.shared.path}/database"):
                if file.endswith(".json"):
                    serverID = int(file.removesuffix(".json"))
                    main: dict = self.load_data(server_id=serverID, serverData=True)
                    db = main
                    try:
                        if path:
                            recursive_add_value(db, path.split("."))
                        else:
                            # Handle the case when no path is provided
                            for k, v in db.items():
                                if isinstance(v, dict):
                                    recursive_add_value(v, path.split("."))
                                elif isinstance(v, list):
                                    for item in v:
                                        recursive_add_value(item, path.split("."))

                        self.save_data(server_id=serverID, update_data=main)
                    
                    except Exception as error:
                        print(f"Could not create a new key/value pair in the DB. {type(error).__name__}: {error}")
                        return False
        else:
            main: dict = self.load_data(server_id=db_id, serverData=True)
            db: dict = main
            try:
                if path:
                    recursive_add_value(db, path.split("."))
                else:
                    # Handle the case when no path is provided
                    for k, v in db.items():
                        if isinstance(v, dict):
                            recursive_add_value(v, path.split("."))
                        elif isinstance(v, list):
                            for item in v:
                                recursive_add_value(item, path.split("."))

                self.save_data(server_id=db_id, update_data=main)
            except Exception as error:
                print(f"Could not create a new key/value pair in the DB. {type(error).__name__}: {error}")
                return False

    def remove_value(self, key: str, path: str = None, db_id: int = None) -> bool:
        if not db_id:
            for file in os.listdir(f"{self.shared.path}/database"):
                if file.endswith(".json"):
                    serverID = int(file.removesuffix(".json"))
                    main: dict = self.load_data(server_id=serverID, serverData=True)
                    db = main
                    try:
                        for p in path.split("."):
                            db = db[p]
                        db.pop(key)
                        self.save_data(server_id=serverID, update_data=main)
                    except Exception as error:
                        print(f"Could not remove key from the DB. {type(error).__name__}: {error}")
                        return
        else:
            main: dict = self.load_data(server_id=db_id, serverData=True)
            db: dict = main            
            try:
                for p in path.split("."):
                    db = db[p]
                db.pop(key)    
                self.save_data(server_id=db_id, update_data=main)
            except Exception as error:
                print(f"Could not remove key from the DB. {type(error).__name__}: {error}")  
                return