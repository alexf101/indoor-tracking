import json
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_docs.docs import DocumentationGenerator


class ApiDocumentation(APIView):
    """
    Gets the documentation for the Fingerprint API endpoints
    """
    def get(self, *args, **kwargs):
        docs = DocumentationGenerator().get_docs()
        return Response(json.loads(docs))