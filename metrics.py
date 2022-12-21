import subprocess
from prometheus_client import Gauge, start_http_server

ENC = "utf-8"
HOSTNAME = (subprocess.check_output("hostname").splitlines()[0]).decode(ENC)
TOP_CMD = "top -bn1".split()
DF_CMD = "df"
INVALID_CHARS = [
    "/",
    "\\",
    "_",
]


def _sanitize(string: str) -> str:
    for char in string:
        if char in INVALID_CHARS:
            return _sanitize(string.replace(char, "."))

    return string


def _get_metric_name(subtype: str, unit: str, subunit: str = None) -> str:
    subtype = _sanitize(subtype)
    unit = _sanitize(unit)

    name = f"{HOSTNAME}_{subtype}_{unit}"
    if subunit:
        name += f"_{subunit}"

    return name


def _get_top_data() -> dict:
    output = subprocess.check_output(TOP_CMD)
    result = {}
    for line in output.splitlines():
        decoded = line.decode(ENC)
        if "%Cpu(s)" in decoded:
            print(f"Found CPU line: {decoded}")
            vals = decoded.split(",")
            for val in vals:
                measurement = val.split()
                unit = measurement[-1]
                measure = float(measurement[-2])
                metric = _get_metric_name("cpu", unit)
                result[metric] = measure
        elif "MiB" in decoded:
            print(f"Found Memory line: {decoded}")
            mem_type = decoded.split()[1].replace(":", "").lower()
            vals = decoded.split(",")
            for val in vals:
                measurement = val.split()
                unit = measurement[-1]
                measure = measurement[-2]
                metric = _get_metric_name(mem_type, unit)
                if measure.lower() != "avail":
                    result[metric] = measure
        elif "Tasks" in decoded:
            print(f"Found tasks line: {decoded}")
            vals = decoded.split(",")
            for val in vals:
                measurement = val.split()
                unit = measurement[-1]
                measure = measurement[-2]
                metric = _get_metric_name("tasks", unit)
                result[metric] = measure
    return result


def _get_df_data() -> dict:
    output = subprocess.check_output(DF_CMD)
    result = {}
    for line in output.splitlines():
        decoded = line.decode(ENC)
        if "Filesystem" not in decoded:
            columns = decoded.split()
            filesystem = columns[0]
            used = int(columns[2])
            available = int(columns[3])
            total = used + available
            percentage = used / total
            result[
                _get_metric_name(subtype="filesystem", unit=filesystem, subunit="used")
            ] = used
            result[
                _get_metric_name(subtype="filesystem", unit=filesystem, subunit="free")
            ] = available
            result[
                _get_metric_name(subtype="filesystem", unit=filesystem, subunit="perc")
            ] = percentage
    return result


if __name__ == "__main__":
    result = _get_df_data()
    for key in result.keys():
        print(f"{key}:{result[key]}")
