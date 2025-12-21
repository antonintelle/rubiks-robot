from subprocess import run
from psutil import users

class SystemTools:
    def shutdown(self):
        subprocess.run(["sudo", "shutdown", "-h", "now"])

    def get_remote_users(self) -> list[dict] :
        return [
            u._asdict()
            for u in psutil.users()
            if u.host
        ]
