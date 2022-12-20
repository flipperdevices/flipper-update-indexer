import re
from .indextypes import FileParser


class qFlipperFileParser(FileParser):
    def parse(self, filename: str) -> None:
        regex = re.compile(r"^(qFlipper\w*)(-.+)*-([0-9.a]+)(-rc\d+)?\.(\w+)$")
        match = regex.match(filename)
        if not match:
            return
        arch = match.group(2)
        extention = match.group(5)
        if extention == "dmg":
            target = "macos"
            file_type = "dmg"
        elif extention == "zip":
            target = "windows"
            file_type = "portable"
        elif extention == "AppImage":
            target = "linux"
            file_type = "AppImage"
        elif extention == "exe":
            target = "windows"
            file_type = "installer"
        else:
            raise Exception(f"Unknown file extention {extention}")
        if extention == "dmg":  # MacOS case
            jsonArch = "amd64"
        else:
            arch = arch.split("-")[1]
            if arch in ["64bit", "x86_64"]:
                jsonArch = "amd64"
            else:
                raise Exception(f"Cannot parse target")
        self.target = target + "/" + jsonArch
        self.type = file_type
