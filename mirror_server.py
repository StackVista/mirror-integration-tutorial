#!/usr/bin/env python
from typing import Any, Dict    # noqa
import json
from http.server import ThreadingHTTPServer    # type: ignore
from http.server import BaseHTTPRequestHandler
import random

random.seed(42)


class RecordingHandler(BaseHTTPRequestHandler):
    api_key = "api_key"

    def do_PUT(self):
        self.send_response(501)

    def do_POST(self):
        print("POST on %s" % self.path)
        if self.path == "/api/connection":
            result = self.handle_test_connection()
            self.json_response(result)
        elif self.path == "/api/field/name":
            result = self.handle_field_names()
            self.json_response(result)
        elif self.path == "/api/field/value":
            result = self.handle_field_values()
            self.json_response(result)
        elif self.path == "/api/metric":
            content_len = int(self.headers.get('content-length', 0))
            payload = self.rfile.read(content_len)
            result = self.handle_metric(json.loads(payload))
            self.json_response(result)
        else:
            self.send_response(501)

    def do_GET(self):
        self.send_response(501)

    def json_response(self, payload: Dict[str, Any]):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('X-Mirror-api-key', RecordingHandler.api_key)
        self.end_headers()
        print(f"response {payload}")
        self.wfile.write(str.encode(json.dumps(payload)))
        return

    def do_HEAD(self):
        self.send_response(501)

    def handle_test_connection(self):
        return {"status": "OK", "_type": "TestConnectionResponse"}

    def handle_field_names(self):
        return {
            "_type": "FieldNamesResponse",
            "fields":
                [
                    {
                        "_type": "FieldDescriptor",
                        "classified": False,
                        "fieldName": "field1",
                        "fieldType": "STRING"
                    }, {
                        "_type": "FieldDescriptor",
                        "classified": False,
                        "fieldName": "field2",
                        "fieldType": "BOOLEAN"
                    }, {
                        "_type": "FieldDescriptor",
                        "classified": False,
                        "fieldName": "field3",
                        "fieldType": "NUMBER"
                    }
                ],
            "isPartial": False
        }

    def handle_field_values(self):
        return {
            "values":
                [
                    {
                        "value": "value1",
                        "_type": "CompleteValue"
                    }, {
                        "value": "cpu.*",
                        "_type": "FieldValuePattern"
                    }
                ],
            "isPartial": False,
            "_type": "FieldValuesResponse"
        }

    def handle_metric(self, payload: Dict[str, Any]):
        start_time = payload['query']['startTime']
        end_time = payload['query']['endTime']
        aggregation = payload['query'].get('aggregation')
        step = int((end_time - start_time) / 50)
        step = step if step > 0 else 1000    # 1 second otherwise
        if aggregation is not None:
            points = [
                [random.random() * 100, timestamp, timestamp + step]
                for i, timestamp in enumerate(range(start_time, end_time, step))
            ]
            return {
                "telemetry":
                    {
                        "points": points,
                        "dataFormat": ["value", "startTimestamp", "endTimestamp"],
                        "isPartial": False,
                        "_type": "AggregatedMetricTelemetry"
                    },
                "_type": "MetricsResponse"
            }
        else:
            points = [
                [random.random() * 100, timestamp]
                for i, timestamp in enumerate(range(start_time, end_time, step))
            ]
            return {
                "telemetry":
                    {
                        "points": points,
                        "dataFormat": ["value", "timestamp"],
                        "isPartial": False,
                        "_type": "RawMetricTelemetry"
                    },
                "_type": "MetricsResponse"
            }


server_address = ("localhost", 7007)

httpd = ThreadingHTTPServer(server_address, RecordingHandler)

print("The sample mirror server is listening on port 7007")
print("Press CTRL-C to stop")
httpd.serve_forever()

httpd.server_close()
