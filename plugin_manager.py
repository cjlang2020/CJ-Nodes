# custom_nodes 下插件的启用/禁用与整体重载。
# 放在 CJ-Nodes 根目录而不是 service/ 下：service/ 里的文件会被节点加载器当节点扫描。
import os
import sys
import logging

import folder_paths

log = logging.getLogger("CJ-Nodes")

SELF = "CJ-Nodes"
DISABLED_SUFFIX = ".disabled"


def comfy_nodes():
    """ComfyUI 根目录的 nodes 模块。
    不能直接 `import nodes`：CJ-Nodes 根目录下也有同名文件，可能被解析到。
    """
    mod = sys.modules.get("nodes")
    if mod is None or not hasattr(mod, "LOADED_MODULE_DIRS"):
        raise RuntimeError("未找到 ComfyUI 的 nodes 模块")
    return mod


def custom_node_dirs():
    dirs = []
    for path in folder_paths.get_folder_paths("custom_nodes"):
        real = os.path.realpath(path)
        if os.path.isdir(real) and real not in dirs:
            dirs.append(real)
    return dirs


def _split(entry):
    """'pack.disabled' -> ('pack', False)；'pack' -> ('pack', True)"""
    if entry.endswith(DISABLED_SUFFIX):
        return entry[: -len(DISABLED_SUFFIX)], False
    return entry, True


def _module_name(entry):
    """与 ComfyUI 加载器 get_module_name 一致：文件去掉扩展名，目录取目录名"""
    name, _ = _split(entry)
    if name.lower().endswith(".py"):
        name = name[:-3]
    return name


def _is_loadable(entry, full):
    if os.path.isdir(full):
        return True
    return entry.lower().endswith(".py") or entry.lower().endswith(".py" + DISABLED_SUFFIX)


def _registered_counts():
    """一次遍历算出每个插件当前注册了多少个节点（大对象上逐个 getattr 太浪费）"""
    counts = {}
    for cls in comfy_nodes().NODE_CLASS_MAPPINGS.values():
        rel = getattr(cls, "RELATIVE_PYTHON_MODULE", None)
        if rel and rel.startswith("custom_nodes."):
            counts[rel] = counts.get(rel, 0) + 1
    return counts


def list_plugins():
    """列出 custom_nodes 下的插件（不含 CJ-Nodes 自身与隐藏目录）"""
    items = []
    counts = _registered_counts()
    for base in custom_node_dirs():
        try:
            entries = os.listdir(base)
        except OSError:
            continue
        for entry in sorted(entries):
            if entry.startswith(".") or entry == "__pycache__":
                continue
            full = os.path.join(base, entry)
            if not _is_loadable(entry, full):
                continue
            name, enabled = _split(entry)
            if name == SELF or not name:
                continue
            items.append({
                "id": entry,
                "name": name,
                "enabled": enabled,
                "is_dir": os.path.isdir(full),
                "dir": base,
                "node_count": counts.get("custom_nodes." + _module_name(entry), 0) if enabled else 0,
            })
    return items


def _resolve(entry_id):
    if not entry_id or entry_id in (".", "..") or os.path.basename(entry_id) != entry_id \
            or "/" in entry_id or "\\" in entry_id:
        raise ValueError(f"非法的插件名: {entry_id}")
    for base in custom_node_dirs():
        full = os.path.abspath(os.path.join(base, entry_id))
        try:
            inside = os.path.commonpath((base, full)) == base
        except ValueError:
            inside = False
        if not inside:
            raise ValueError(f"路径越界: {entry_id}")
        if os.path.exists(full):
            name, enabled = _split(entry_id)
            if name == SELF:
                raise ValueError("不能操作 CJ-Nodes 自身")
            return base, full, name, enabled
    raise ValueError(f"未找到插件: {entry_id}")


def set_enabled(entry_id, enabled):
    """通过给目录/文件加或去掉 .disabled 后缀来启用/禁用"""
    base, full, name, current = _resolve(entry_id)
    if current == enabled:
        return {"id": entry_id, "name": name, "enabled": enabled, "changed": False}
    target_name = name if enabled else name + DISABLED_SUFFIX
    target = os.path.join(base, target_name)
    if os.path.exists(target):
        raise ValueError(f"目标名称已存在，无法重命名: {target_name}")
    os.rename(full, target)
    log.info("[CJ-Nodes] 插件 %s 已%s -> %s", name, "启用" if enabled else "关闭", target_name)
    return {"id": target_name, "name": name, "enabled": enabled, "changed": True}


def _purge_modules(entry, full):
    """清掉某个插件在 sys.modules 里的缓存。
    加载器用的是 importlib 自己造的模块名：目录为「路径把点换成 _x_」，文件为「路径去扩展名」。
    """
    keys = [full.replace(".", "_x_"), os.path.splitext(full)[0]]
    for key in keys:
        for mod in list(sys.modules):
            if mod == key or mod.startswith(key + "."):
                sys.modules.pop(mod, None)


def _unload_external(cn):
    """把外部插件注册的节点映射/模块缓存/目录登记全部摘掉（保留核心节点与 CJ-Nodes）"""
    removed = []
    for key, cls in list(cn.NODE_CLASS_MAPPINGS.items()):
        rel = getattr(cls, "RELATIVE_PYTHON_MODULE", None)
        if not rel or not rel.startswith("custom_nodes.") or rel == "custom_nodes." + SELF:
            continue
        cn.NODE_CLASS_MAPPINGS.pop(key, None)
        cn.NODE_DISPLAY_NAME_MAPPINGS.pop(key, None)
        removed.append(key)
    for base in custom_node_dirs():
        try:
            entries = os.listdir(base)
        except OSError:
            continue
        for entry in entries:
            if entry.startswith(".") or entry == "__pycache__":
                continue
            name, _ = _split(entry)
            if name == SELF:
                continue
            full = os.path.join(base, entry)
            if not _is_loadable(entry, full):
                continue
            cn.EXTENSION_WEB_DIRS.pop(_module_name(entry), None)
            cn.LOADED_MODULE_DIRS.pop(_module_name(entry), None)
            _purge_modules(entry, full)
    return removed


def _register_web_dirs(cn):
    """给这次重新加载出来、但启动时没登记的 web 目录补上 /extensions 静态路由。
    注意：插件自己注册的 HTTP 路由不会因此生效，那部分仍需重启。
    """
    try:
        from aiohttp import web
        from server import PromptServer
        app = PromptServer.instance.app
    except Exception as exc:
        log.warning("[CJ-Nodes] 无法获取 server app，跳过 web 目录登记: %s", exc)
        return []
    existing = set()
    for res in app.router.resources():
        canonical = getattr(res, "canonical", None)
        if canonical:
            existing.add(canonical.rstrip("/"))
    added = []
    for name, web_dir in list(cn.EXTENSION_WEB_DIRS.items()):
        prefix = "/extensions/" + name
        if prefix.rstrip("/") in existing or not os.path.isdir(web_dir):
            continue
        try:
            app.add_routes([web.static(prefix, web_dir)])
            added.append(name)
        except Exception as exc:
            log.warning("[CJ-Nodes] 注册静态目录失败 %s: %s", prefix, exc)
    return added


async def reload_plugins():
    """重新加载 custom_nodes 下的所有插件（跳过 CJ-Nodes 与已禁用的）"""
    cn = comfy_nodes()
    protected = {name for name, cls in cn.NODE_CLASS_MAPPINGS.items()
                 if getattr(cls, "RELATIVE_PYTHON_MODULE", None) == "custom_nodes." + SELF
                 or not getattr(cls, "RELATIVE_PYTHON_MODULE", None)}
    removed = _unload_external(cn)

    args = getattr(cn, "args", None)
    whitelist = list(getattr(args, "whitelist_custom_nodes", []) or [])
    disable_all = bool(getattr(args, "disable_all_custom_nodes", False))

    loaded, failed, skipped = [], [], []
    for base in custom_node_dirs():
        try:
            entries = sorted(os.listdir(base))
        except OSError:
            continue
        for entry in entries:
            if entry.startswith(".") or entry == "__pycache__" or entry.endswith(DISABLED_SUFFIX):
                continue
            name, _ = _split(entry)
            if name == SELF:
                continue
            full = os.path.join(base, entry)
            if not _is_loadable(entry, full):
                continue
            if disable_all and entry not in whitelist:
                skipped.append(name)
                continue
            ok = await cn.load_custom_node(full, ignore=protected, module_parent="custom_nodes")
            (loaded if ok else failed).append(name)

    web_added = _register_web_dirs(cn)
    log.info("[CJ-Nodes] 插件重载完成：卸载 %d 个节点类，加载 %d 个包，失败 %d 个",
             len(removed), len(loaded), len(failed))
    return {
        "removed_nodes": len(removed),
        "loaded": sorted(loaded),
        "failed": sorted(failed),
        "skipped": sorted(skipped),
        "web_added": sorted(web_added),
    }
