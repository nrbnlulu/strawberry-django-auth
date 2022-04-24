from django.urls import path
from strawberry.django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True)))]
