from rest_framework import viewsets
from rest_framework.response import Response
from logging import getLogger

logger = getLogger(__name__)

def filter_query_set(request, queryset):
    query_dic = {}
    values = []
    distinct = False
    order_by, limit = None, None
    for k, v in request.GET.iteritems():
        if k == 'order_by':
            order_by = v
        elif k == 'limit':
            limit = v
        elif k == 'values':
            for value in request.GET.getlist(k):
                values.append(value)
        elif k == 'distinct':
            distinct = True
        else:
            query_dic[k] = v
    query = queryset.filter(**query_dic)
    if len(values) > 0:
        query = query.values(*values)
    if distinct:
        query = query.distinct()
    if order_by is not None:
        query = query.order_by(order_by)
    if limit is not None:
        query = query[:limit]
    return query, len(values) > 0


class QueryableViewSet(viewsets.ModelViewSet):

    def list(self, request, *args, **kwargs):
        query, is_dictionary = filter_query_set(request, self.queryset)
        if is_dictionary:
            return Response(query)
        else:
            serializer = self.serializer_class(query, context={'request': request}, many=True)
            return Response(serializer.data)
