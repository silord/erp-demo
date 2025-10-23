"""Configuration helper for sync integration testing.

Loads from environment variables or a local JSON file `sync_config.json` in the project
root. Provides a dataclass with defaults populated from the provided test address.
"""
from dataclasses import dataclass, asdict
import os
import json
from typing import Optional


@dataclass
class SyncConfig:
    token_url: str
    corp_id: Optional[int]
    app_id: Optional[str]
    app_secret: Optional[str]
    # optional: target sync endpoint to post orders to (not used by default)
    sync_target: Optional[str] = None


DEFAULT = SyncConfig(
    token_url='https://open.handday.cn/grantauth/gettoken',
    corp_id=150046974,
    app_id='06e1014e6bfc11ee93b40c42a1db2810',
    app_secret='262c405ee2d13482ea03ad7d83e9ebfee02d6584e4faa19aa172829569af2c3f',
    sync_target=None,
)


def load_config(project_root: str = None) -> SyncConfig:
    """Load configuration from env vars or a `sync_config.json` file in project_root.

    Precedence: environment variables > sync_config.json > DEFAULT
    Supported env vars:
      SYNC_TOKEN_URL, SYNC_CORP_ID, SYNC_APP_ID, SYNC_APP_SECRET, SYNC_TARGET
    """
    # env overrides
    token_url = os.environ.get('SYNC_TOKEN_URL')
    corp_id = os.environ.get('SYNC_CORP_ID')
    app_id = os.environ.get('SYNC_APP_ID')
    app_secret = os.environ.get('SYNC_APP_SECRET')
    sync_target = os.environ.get('SYNC_TARGET')

    # try file
    cfg_path = None
    if project_root:
        cfg_path = os.path.join(project_root, 'sync_config.json')
    else:
        cfg_path = os.path.join(os.getcwd(), 'sync_config.json')

    file_cfg = {}
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                file_cfg = json.load(f)
        except Exception:
            file_cfg = {}

    def pick(val, key, default):
        return val if val is not None else file_cfg.get(key, default)

    token_url = pick(token_url, 'token_url', DEFAULT.token_url)
    corp_id = pick(corp_id, 'corp_id', DEFAULT.corp_id)
    app_id = pick(app_id, 'app_id', DEFAULT.app_id)
    app_secret = pick(app_secret, 'app_secret', DEFAULT.app_secret)
    sync_target = pick(sync_target, 'sync_target', DEFAULT.sync_target)

    # coerce types
    try:
        if corp_id is not None:
            corp_id = int(corp_id)
    except Exception:
        corp_id = DEFAULT.corp_id

    return SyncConfig(token_url=token_url, corp_id=corp_id, app_id=app_id, app_secret=app_secret, sync_target=sync_target)


def save_sample_config(path: str = None):
    """Write a sample `sync_config.json` to the given path (default cwd)."""
    p = path or os.path.join(os.getcwd(), 'sync_config.json')
    data = asdict(DEFAULT)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return p


if __name__ == '__main__':
    print('Default config:')
    print(json.dumps(asdict(DEFAULT), indent=2, ensure_ascii=False))
