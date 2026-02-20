DOMAIN = "history_archiver"

CONF_GLOBAL_INTERVAL = "global_interval"
CONF_EXPORT_PATH = "export_path"

DEFAULT_GLOBAL_INTERVAL = 10  # seconds
DEFAULT_EXPORT_PATH = "history_archiver_exports"

DATA_DB = f"{DOMAIN}_db"
DATA_PROFILE_MANAGER = f"{DOMAIN}_profile_manager"
DATA_ENTITY_MANAGER = f"{DOMAIN}_entity_manager"
DATA_SCHEDULER = f"{DOMAIN}_scheduler"
DATA_EXPORT_ENGINE = f"{DOMAIN}_export_engine"

ATTR_PROFILE_ID = "profile_id"
ATTR_PROFILE_NAME = "profile_name"

METADATA_FIELDS = [
    "manufacturer",
    "model",
    "sw_version",
    "hw_version",
    "device_class",
    "entity_category",
    "integration_domain",
    "area_name",
    "device_name",
    "entity_name",
]

EXPORT_FORMAT_CSV = "csv"
EXPORT_FORMAT_JSON = "json"
EXPORT_FORMAT_HTML = "html"
EXPORT_FORMAT_XLSX = "xlsx"
EXPORT_FORMAT_SQLITE = "sqlite"
EXPORT_FORMAT_PARQUET = "parquet"
EXPORT_FORMAT_FEATHER = "feather"
EXPORT_FORMAT_ARROW = "arrow"

SUPPORTED_EXPORT_FORMATS = [
    EXPORT_FORMAT_CSV,
    EXPORT_FORMAT_JSON,
    EXPORT_FORMAT_HTML,
    EXPORT_FORMAT_XLSX,
    EXPORT_FORMAT_SQLITE,
    EXPORT_FORMAT_PARQUET,
    EXPORT_FORMAT_FEATHER,
    EXPORT_FORMAT_ARROW,
]

DATA_ACCURACY_RAW = "raw"
DATA_ACCURACY_MEAN = "mean"
DATA_ACCURACY_WEIGHTED_MEAN = "weighted_mean"

DB_FILENAME = "history.db"
DB_SCHEMA_VERSION = 1
