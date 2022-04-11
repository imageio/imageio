from typing import List, Dict

class FileExtension:
    def __init__(
        self,
        *,
        extension: str,
        priority: List[str],
        name: str = None,
        description: str = None,
        external_link: str = None
    ) -> None: ...
    def reset(self) -> None: ...

extension_list: List[FileExtension]
known_extensions: Dict[str, List[FileExtension]]
video_extensions: List[FileExtension]
