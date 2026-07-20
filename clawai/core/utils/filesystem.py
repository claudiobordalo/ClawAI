from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class FileSystem:
    """
    Utility class for file system operations.
    """

    @staticmethod
    def ensure_directory_exists(path: str | Path) -> None:
        """Ensure that a directory exists, creating it if necessary."""
        path_obj = Path(path)
        try:
            path_obj.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Failed to create directory '{path}': {e}")

    @staticmethod
    def file_exists(path: str | Path) -> bool:
        """Check if a file exists at the given path."""
        return Path(path).is_file()

    @staticmethod
    def is_directory_empty(directory_path: str | Path) -> bool:
        """
        Check if a directory is empty.
        
        Args:
            directory_path (str | Path): The path to check
            
        Returns:
            bool: True if the directory exists and is empty, False otherwise
        """
        try:
            dir_path = Path(directory_path)
            return dir_path.is_dir() and not any(dir_path.iterdir())
        except OSError:
            # If we can't access or determine the directory state,
            # assume it's not empty (safer approach)
            return False

    @staticmethod
    def get_file_size(path: str | Path) -> int:
        """Get file size in bytes."""
        try:
            stat_result = os.stat(str(path))
            return stat_result.st_size
        except OSError as e:
            raise RuntimeError(f"Failed to get file size for '{path}': {e}")

    @staticmethod
    def read_file_content(file_path: str | Path) -> str:
        """Read content from a text file."""
        try:
            with open(str(file_path), "r", encoding="utf-8") as f:
                return f.read()
        except OSError as e:
            raise RuntimeError(f"Failed to read file '{file_path}': {e}")

    @staticmethod
    def write_file_content(
        file_path: str | Path,
        content: str,
        ensure_directory_exists: bool = True,
    ) -> None:
        """Write content to a text file."""
        if ensure_directory_exists:
            FileSystem.ensure_directory_exists(os.path.dirname(str(file_path)))

        try:
            with open(str(file_path), "w", encoding="utf-8") as f:
                f.write(content)
        except OSError as e:
            raise RuntimeError(f"Failed to write file '{file_path}': {e}")

    @staticmethod
    def get_file_extension(path: str | Path) -> str:
        """Get the extension of a file."""
        return Path(path).suffix

    @staticmethod
    def list_files(directory_path: str | Path, pattern: str = "*") -> list[Path]:
        """
        List files in directory matching a glob pattern.
        
        Args:
            directory_path (str | Path): Directory to search
            pattern (str): Glob pattern for file filtering
            
        Returns:
            list[Path]: List of matched file paths
        """
        try:
            dir_path = Path(directory_path)
            if not dir_path.is_dir():
                raise NotADirectoryError(f"'{directory_path}' is not a directory")
            
            return [f for f in dir_path.glob(pattern) if f.is_file()]
        except OSError as e:
            raise RuntimeError(f"Failed to list files in '{directory_path}': {e}")

    @staticmethod
    def get_directory_size(directory_path: str | Path) -> int:
        """
        Calculate total size of all files in a directory.
        
        Args:
            directory_path (str | Path): Directory path
            
        Returns:
            int: Total size in bytes
        """
        try:
            dir_path = Path(directory_path)
            
            if not dir_path.is_dir():
                raise NotADirectoryError(f"'{directory_path}' is not a directory")
                
            total_size = 0
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    
            return total_size
            
        except OSError as e:
            raise RuntimeError(f"Failed to calculate size of '{directory_path}': {e}")

    @staticmethod
    def copy_file(source: str | Path, destination: str | Path) -> None:
        """Copy a file from source to destination."""
        import shutil
        
        try:
            # Ensure the directory exists for the destination
            FileSystem.ensure_directory_exists(os.path.dirname(str(destination)))
            
            shutil.copy2(str(source), str(destination))
        except OSError as e:
            raise RuntimeError(f"Failed to copy '{source}' -> '{destination}': {e}")

    @staticmethod
    def move_file(source: str | Path, destination: str | Path) -> None:
        """Move a file from source to destination."""
        import shutil
        
        try:
            # Ensure the directory exists for the destination
            FileSystem.ensure_directory_exists(os.path.dirname(str(destination)))
            
            shutil.move(str(source), str(destination))
        except OSError as e:
            raise RuntimeError(f"Failed to move '{source}' -> '{destination}': {e}")

    @staticmethod
    def delete_file(file_path: str | Path) -> None:
        """Delete a file."""
        try:
            os.remove(str(file_path))
        except OSError as e:
            # If the error is that the file doesn't exist, it's not an issue for deletion
            if "No such file or directory" in str(e):
                return  # File already deleted - no problem
                
            raise RuntimeError(f"Failed to delete '{file_path}': {e}")

    @staticmethod
    def create_symlink(source: str | Path, destination: str | Path) -> None:
        """Create a symbolic link."""
        try:
            os.symlink(str(source), str(destination))
        except OSError as e:
            raise RuntimeError(f"Failed to create symlink '{destination}' -> '{source}': {e}")

    @staticmethod
    def is_symlink(path: str | Path) -> bool:
        """Check if a path points to a symbolic link."""
        return os.path.islink(str(path))

    @staticmethod
    def get_real_path(path: str | Path) -> Path:
        """
        Get the real path of a file or directory, resolving symlinks.
        
        Args:
            path (str | Path): The path
            
        Returns:
            Path: Resolved real path
        """
        return Path(os.path.realpath(str(path)))