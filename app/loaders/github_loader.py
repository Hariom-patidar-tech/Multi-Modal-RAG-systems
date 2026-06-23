import os
import shutil
import stat
import tempfile
from git import Repo
from app.core.logger import logger
from typing import List, Dict, Any


def _remove_readonly(func, path, exc_info):
    
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        logger.warning(f"Could not remove {path} even after chmod: {str(e)}")


class GitHubLoader:
    def __init__(self):
        self.supported_extensions = {
            '.py', '.js', '.ts', '.tsx', '.jsx', '.json', 
            '.md', '.txt', '.yaml', '.yml', '.sql', '.html', '.css'
        }
        self.ignored_dirs = {
            '.git', '__pycache__', 'node_modules', 'venv', 
            '.venv', 'env', 'dist', 'build', '.idea', '.vscode'
        }

    def load(self, repo_url: str) -> List[Dict[str, Any]]:
        
        logger.info(f"Starting GitHub Repository deep-scan for: {repo_url}")
        repo_files_data = []

        temp_dir = tempfile.mkdtemp(prefix="rag_git_")
        repo = None
        
        try:
            logger.info(f"Cloning repository into temporary directory: {temp_dir}")
            repo = Repo.clone_from(repo_url, temp_dir, depth=1)
            logger.info("Clone completed successfully. Parsing codebase...")

            for root, dirs, files in os.walk(temp_dir):
                dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

                for file in files:
                    file_path = os.path.join(root, file)
                    filename, file_extension = os.path.splitext(file)

                    if file_extension.lower() in self.supported_extensions:
                        relative_path = os.path.relpath(file_path, temp_dir)
                        
                        try:
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                                
                            if content.strip():
                                repo_files_data.append({
                                    "file_path": relative_path,
                                    "text": f"--- File: {relative_path} ---\n\n{content.strip()}"
                                })
                        except Exception as file_err:
                            logger.warning(f"Skipping file {relative_path} due to read error: {str(file_err)}")
                            continue

            logger.info(f"Deep scan finished. Total code files extracted: {len(repo_files_data)}")
            return repo_files_data

        except Exception as e:
            logger.error(f"Critical error during GitHub code extraction: {str(e)}")
            raise Exception(f"GitHub Repository Loader Failed: {str(e)}")
            
        finally:
           
            if repo is not None:
                try:
                    repo.close()
                except Exception:
                    pass

            
            if os.path.exists(temp_dir):
                logger.info(f"Cleaning up temporary git directory: {temp_dir}")
                try:
                    shutil.rmtree(temp_dir, onerror=_remove_readonly)
                except Exception as cleanup_err:
                    
                    logger.warning(f"Temp directory cleanup failed (non-fatal): {str(cleanup_err)}")