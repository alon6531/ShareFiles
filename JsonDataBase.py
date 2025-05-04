import json

class JsonDataBase:
    def __init__(self, filename="groups.json"):
        self.filename = filename
        self.groups = self.load()

    def load(self):
        """Load groups from the JSON file."""
        try:
            with open(self.filename, 'r') as file:
                data = json.load(file)
                return data.get('groups', [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save(self):
        """Save groups to the JSON file."""
        with open(self.filename, 'w') as file:
            json.dump({"groups": self.groups}, file, indent=4)

    def add_group(self, group_name, password):
        """Add a new group with password."""
        if not any(g['name'] == group_name for g in self.groups):
            self.groups.append({"name": group_name, "password": password})
            self.save()

    def get_all_groups(self):
        """Return all group names."""
        return [g['name'] for g in self.groups]

    def verify_password(self, group_name, password):
        """Verify password for a group."""
        for group in self.groups:
            if group['name'] == group_name:
                return group['password'] == password
        return False
