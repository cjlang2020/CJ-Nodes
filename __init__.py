import os
import mimetypes
from pathlib import Path
from aiohttp import web
from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
import nodes as comfy_nodes

WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "web")

JS_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "js")
comfy_nodes.EXTENSION_WEB_DIRS["CJ-Nodes"] = JS_DIR

mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

CJ_WEB_PATH = Path(__file__).parent / 'web'
_CJ_WEB_REAL = CJ_WEB_PATH.resolve()

def _is_safe_child(base_real: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(base_real)
        return True
    except ValueError:
        return False

from server import PromptServer
routes = PromptServer.instance.routes

import folder_paths

@routes.post('/CJ-Nodes/api/open-directory')
async def open_directory(request):
    try:
        data = await request.json()
        dir_type = data.get('type', '')
        if dir_type == 'local-resources':
            path = str(Path(folder_paths.get_output_directory()).resolve())
        elif dir_type == 'workflows':
            user_id = PromptServer.instance.user_manager.get_request_user_id(request)
            path = str(Path(folder_paths.get_user_directory()).resolve() / user_id / "workflows")
        else:
            return web.json_response({'error': 'Invalid type'}, status=400)
        import subprocess
        subprocess.Popen(['explorer', path])
        return web.json_response({'ok': True})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

@routes.get('/CJ-Nodes')
async def serve_cj_nodes_index(request):
    for filename in ['index.html', 'index.html']:
        index_path = CJ_WEB_PATH / filename
        if index_path.exists():
            return web.FileResponse(index_path)
    return web.Response(text="CJ-Nodes UI not found", status=404)

@routes.get('/CJ-Nodes/{path:.*}')
async def serve_cj_nodes_static(request):
    path = request.match_info.get('path', '')
    file_path = CJ_WEB_PATH / path

    if not _is_safe_child(_CJ_WEB_REAL, file_path):
        return web.Response(text="Invalid path", status=403)

    if file_path.is_dir():
        for index_name in ['index.html']:
            index_path = file_path / index_name
            if index_path.exists():
                return web.FileResponse(index_path)

    if file_path.exists() and file_path.is_file():
        return web.FileResponse(file_path)

    return web.Response(text="File not found", status=404)

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
