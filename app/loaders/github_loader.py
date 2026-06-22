import os
import shutil
import stat
import tempfile
from git import Repo
from app.core.logger import logger
from typing import List, Dict, Any


def _remove_readonly(func, path, exc_info):
    """
    Windows par Git ki .git\\objects\\pack\\* files read-only attribute ke saath
    bani hoti hain, isliye shutil.rmtree() unhe delete nahi kar pata
    (WinError 5: Access is denied). Yeh handler attribute clear karke retry karta hai.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        logger.warning(f"Could not remove {path} even after chmod: {str(e)}")


class GitHubLoader:
    def __init__(self):
        # Industrial standard: Jin extensions ka code hume extract karna hai
        self.supported_extensions = {
            '.py', '.js', '.ts', '.tsx', '.jsx', '.json', 
            '.md', '.txt', '.yaml', '.yml', '.sql', '.html', '.css'
        }
        # Trash/heavy directories jinka content RAG me nahi bhejna hai
        self.ignored_dirs = {
            '.git', '__pycache__', 'node_modules', 'venv', 
            '.venv', 'env', 'dist', 'build', '.idea', '.vscode'
        }

    def load(self, repo_url: str) -> List[Dict[str, Any]]:
        """
        GitHub Repository ko temporarily clone karta hai aur saari valid 
        code files ka text aur path extract karke return karta hai.
        """
        logger.info(f"Starting GitHub Repository deep-scan for: {repo_url}")
        repo_files_data = []

        # 1. Ek temporary directory create karein jahan repo clone hoga
        temp_dir = tempfile.mkdtemp(prefix="rag_git_")
        repo = None
        
        try:
            logger.info(f"Cloning repository into temporary directory: {temp_dir}")
            # Clone repo (shallow clone with depth=1 taaki fast download ho)
            repo = Repo.clone_from(repo_url, temp_dir, depth=1)
            logger.info("Clone completed successfully. Parsing codebase...")

            # 2. Directory Tree ko recursively walk (traverse) karein
            for root, dirs, files in os.walk(temp_dir):
                # Ignored directories ko skip karein inplace modification se
                dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

                for file in files:
                    file_path = os.path.join(root, file)
                    filename, file_extension = os.path.splitext(file)

                    if file_extension.lower() in self.supported_extensions:
                        # Repository ke andar ka relative path calculate karein (for citation/metadata)
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
            # 2.5 GitPython ka internal git process close karo, taaki Windows par
            # .git\objects\pack\* files par file-lock na rahe (cleanup se pehle zaroori)
            if repo is not None:
                try:
                    repo.close()
                except Exception:
                    pass

            # 3. Clean-up: Storage space bachane ke liye temp directory ko delete karna zaroori hai
            # onerror handler Windows ke read-only .git files ko bhi clear kar deta hai
            if os.path.exists(temp_dir):
                logger.info(f"Cleaning up temporary git directory: {temp_dir}")
                try:
                    shutil.rmtree(temp_dir, onerror=_remove_readonly)
                except Exception as cleanup_err:
                    # Cleanup fail hone se poori request fail nahi honi chahiye —
                    # sirf warning log karo, data already process ho chuka hai
                    logger.warning(f"Temp directory cleanup failed (non-fatal): {str(cleanup_err)}")