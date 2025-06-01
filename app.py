from flask import Flask, request, send_file, jsonify
import subprocess
import tempfile
import os

app = Flask(__name__)

PS_TEMPLATE = """
%!PS
<</BarcodeType /{barcode_type} /Options () /Value ({barcode_data})>>
/uk.co.terryburton.bwipp findresource exec
showpage
"""

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    barcode_data = data.get("data", "")
    barcode_type = data.get("type", "ean13")
    output_format = data.get("format", "pdf")

    if not barcode_data:
        return jsonify({"error": "No barcode data provided"}), 400

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ps_path = os.path.join(tmpdir, "barcode.ps")
            output_path = os.path.join(tmpdir, f"barcode.{output_format}")

            with open(ps_path, "w") as f:
                f.write(PS_TEMPLATE.format(barcode_type=barcode_type, barcode_data=barcode_data))

            gs_device = {
                "pdf": "pdfwrite",
                "eps": "eps2write",
                "svg": "svg"
            }.get(output_format, "pdfwrite")

            subprocess.run([
                "gs",
                "-dBATCH",
                "-dNOPAUSE",
                "-sDEVICE=" + gs_device,
                f"-sOutputFile={output_path}",
                ps_path
            ], check=True)

            return send_file(output_path, as_attachment=True)

    except subprocess.CalledProcessError:
        return jsonify({"error": "Ghostscript failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def health():
    return "BarcodeGen API is running", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
