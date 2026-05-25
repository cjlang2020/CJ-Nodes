import os
import mimetypes
from pathlib import Path
from typing import Optional
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

LOCAL_RESOURCES_ROOT = Path(folder_paths.get_output_directory()).resolve()
_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif', '.svg', '.ico'}
_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.ogg', '.aac', '.wma', '.m4a'}
_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.mpeg', '.mpg'}

def _is_under_pictures(path: Path) -> bool:
    try:
        path.resolve().relative_to(LOCAL_RESOURCES_ROOT)
        return True
    except ValueError:
        return False

def _get_file_type(path: Path) -> Optional[str]:
    suffix = path.suffix.lower()
    if suffix in _IMAGE_EXTENSIONS:
        return 'image'
    if suffix in _AUDIO_EXTENSIONS:
        return 'audio'
    if suffix in _VIDEO_EXTENSIONS:
        return 'video'
    return None

@routes.get('/CJ-Nodes/api/local-resources/list')
async def local_resources_list(request):
    rel_path = request.query.get('path', '')
    target = (LOCAL_RESOURCES_ROOT / rel_path).resolve()

    if not _is_under_pictures(target):
        return web.json_response({'error': 'Access denied'}, status=403)
    if not target.is_dir():
        return web.json_response({'error': 'Not a directory'}, status=400)

    entries = []
    for child in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        if child.name.startswith('.'):
            continue
        is_dir = child.is_dir()
        file_type = None if is_dir else _get_file_type(child)
        entry = {
            'name': child.name,
            'isDirectory': is_dir,
            'fileType': file_type,
        }
        if file_type == 'image':
            child_rel = child.relative_to(LOCAL_RESOURCES_ROOT).as_posix()
            entry['thumbUrl'] = f'/CJ-Nodes/api/local-resources/image?path={child_rel}'
        entries.append(entry)

    current_rel = target.relative_to(LOCAL_RESOURCES_ROOT).as_posix()
    parent_rel = target.parent.relative_to(LOCAL_RESOURCES_ROOT).as_posix() if target != LOCAL_RESOURCES_ROOT else None

    return web.json_response({
        'entries': entries,
        'currentPath': current_rel if current_rel != '.' else '',
        'parentPath': parent_rel if parent_rel != '.' else None,
    })

@routes.get('/CJ-Nodes/api/local-resources/image')
async def local_resources_image(request):
    rel_path = request.query.get('path', '')
    target = (LOCAL_RESOURCES_ROOT / rel_path).resolve()

    if not _is_under_pictures(target):
        return web.Response(text='Access denied', status=403)
    if not target.is_file() or _get_file_type(target) != 'image':
        return web.Response(text='Not an image', status=400)

    return web.FileResponse(target)

@routes.post('/CJ-Nodes/api/local-resources/import')
async def local_resources_import(request):
    data = await request.json()
    rel_path = data.get('path', '')
    target = (LOCAL_RESOURCES_ROOT / rel_path).resolve()

    if not _is_under_pictures(target):
        return web.json_response({'error': 'Access denied'}, status=403)
    if not target.is_file():
        return web.json_response({'error': 'Not a file'}, status=400)

    file_type = _get_file_type(target)
    if not file_type:
        return web.json_response({'error': 'Unsupported file type'}, status=400)

    return web.json_response({
        'filename': rel_path,
        'fileType': file_type,
    })

def _resolve_path(rel_path: str) -> Optional[Path]:
    target = (LOCAL_RESOURCES_ROOT / rel_path).resolve()
    if not _is_under_pictures(target):
        return None
    return target

@routes.post('/CJ-Nodes/api/local-resources/rename')
async def local_resources_rename(request):
    data = await request.json()
    target = _resolve_path(data.get('path', ''))
    new_name = data.get('newName', '')
    if not target or not target.exists():
        return web.json_response({'error': 'File not found'}, status=404)
    if not new_name or '/' in new_name or '\\' in new_name:
        return web.json_response({'error': 'Invalid name'}, status=400)
    new_path = target.parent / new_name
    if new_path.exists():
        return web.json_response({'error': 'Target already exists'}, status=409)
    target.rename(new_path)
    return web.json_response({'ok': True})

@routes.post('/CJ-Nodes/api/local-resources/move')
async def local_resources_move(request):
    data = await request.json()
    target = _resolve_path(data.get('path', ''))
    dest_rel = data.get('destDir', '')
    if not target or not target.exists():
        return web.json_response({'error': 'File not found'}, status=404)
    dest_dir = _resolve_path(dest_rel)
    if not dest_dir or not dest_dir.is_dir():
        return web.json_response({'error': 'Invalid destination'}, status=400)
    new_path = dest_dir / target.name
    if new_path.exists():
        return web.json_response({'error': 'Target already exists'}, status=409)
    target.rename(new_path)
    return web.json_response({'ok': True})

@routes.post('/CJ-Nodes/api/local-resources/delete')
async def local_resources_delete(request):
    data = await request.json()
    target = _resolve_path(data.get('path', ''))
    if not target or not target.exists():
        return web.json_response({'error': 'File not found'}, status=404)
    if target.is_dir():
        import shutil
        shutil.rmtree(target)
    else:
        target.unlink()
    return web.json_response({'ok': True})

WORKFLOWS_BASE = Path(folder_paths.get_user_directory()).resolve()

def _get_user_workflows_path(request) -> Path:
    user_id = PromptServer.instance.user_manager.get_request_user_id(request)
    return WORKFLOWS_BASE / user_id / "workflows"

@routes.get('/CJ-Nodes/api/workflows/list')
async def workflows_list(request):
    try:
        wf_root = _get_user_workflows_path(request)
        wf_root.mkdir(parents=True, exist_ok=True)
        rel_path = request.query.get('path', '')
        target = (wf_root / rel_path).resolve()
        try:
            target.relative_to(wf_root)
        except ValueError:
            return web.json_response({'error': 'Access denied'}, status=403)
        if not target.is_dir():
            return web.json_response({'error': 'Not found'}, status=404)
        entries = []
        for child in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if child.name.startswith('.'):
                continue
            entries.append({
                'name': child.name,
                'isDirectory': child.is_dir(),
                'isWorkflow': child.suffix.lower() == '.json' if not child.is_dir() else False,
            })
        current_rel = target.relative_to(wf_root).as_posix()
        parent_rel = target.parent.relative_to(wf_root).as_posix() if target != wf_root else None
        return web.json_response({
            'entries': entries,
            'currentPath': current_rel if current_rel != '.' else '',
            'parentPath': parent_rel if parent_rel != '.' else None,
            '_workflowsRoot': str(wf_root),
        })
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

def _resolve_wf_path(request, rel_path: str) -> Optional[Path]:
    try:
        wf_root = _get_user_workflows_path(request)
        target = (wf_root / rel_path).resolve()
        target.relative_to(wf_root)
        return target
    except (ValueError, OSError):
        return None

@routes.post('/CJ-Nodes/api/workflows/rename')
async def workflows_rename(request):
    try:
        data = await request.json()
        target = _resolve_wf_path(request, data.get('path', ''))
        new_name = data.get('newName', '')
        if not target or not target.exists():
            return web.json_response({'error': 'Not found'}, status=404)
        if not new_name or '/' in new_name or '\\' in new_name:
            return web.json_response({'error': 'Invalid name'}, status=400)
        new_path = target.parent / new_name
        if new_path.exists():
            return web.json_response({'error': 'Target already exists'}, status=409)
        target.rename(new_path)
        return web.json_response({'ok': True})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

@routes.post('/CJ-Nodes/api/workflows/move')
async def workflows_move(request):
    try:
        data = await request.json()
        target = _resolve_wf_path(request, data.get('path', ''))
        dest_rel = data.get('destDir', '')
        if not target or not target.exists():
            return web.json_response({'error': 'Not found'}, status=404)
        dest_dir = _resolve_wf_path(request, dest_rel)
        if not dest_dir or not dest_dir.is_dir():
            return web.json_response({'error': 'Invalid destination'}, status=400)
        new_path = dest_dir / target.name
        if new_path.exists():
            return web.json_response({'error': 'Target already exists'}, status=409)
        target.rename(new_path)
        return web.json_response({'ok': True})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

@routes.post('/CJ-Nodes/api/workflows/delete')
async def workflows_delete(request):
    try:
        data = await request.json()
        target = _resolve_wf_path(request, data.get('path', ''))
        if not target or not target.exists():
            return web.json_response({'error': 'Not found'}, status=404)
        if target.is_dir():
            import shutil
            shutil.rmtree(target)
        else:
            target.unlink()
        return web.json_response({'ok': True})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

@routes.get('/CJ-Nodes/api/workflows/read')
async def workflows_read(request):
    try:
        rel_path = request.query.get('path', '')
        target = _resolve_wf_path(request, rel_path)
        if not target or not target.is_file() or target.suffix.lower() != '.json':
            return web.json_response({'error': 'Not found'}, status=404)
        return web.FileResponse(target)
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
