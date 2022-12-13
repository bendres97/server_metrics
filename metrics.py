import subprocess
from prometheus_client import Gauge, start_http_server

ENC = "utf-8"
HOSTNAME = (subprocess.check_output("hostname").splitlines()[0]).decode(ENC)
TOP_CMD = "top -bn1".split()


def _sanitize(string: str) -> str:
    string = string.replace("/", ".")
    string = string.replace("\\", ".")
    string = string.replace("_", ".")

    return string


def _get_metric_name(subtype: str, unit: str) -> str:
    subtype = _sanitize(subtype)
    unit = _sanitize(unit)

    return f"{HOSTNAME}_{subtype}_{unit}"


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


if __name__ == "__main__":
    result = _get_top_data()
    print(result)
