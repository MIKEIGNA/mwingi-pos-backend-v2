from django.urls import path

from api import views

cluster_url_patterns = [
    path(
        'api/clusters/lean/',
        views.StoreClusterLeanIndexView.as_view(),
        name='store-cluster-index-lean'
    ),
    path(
        'api/clusters/',
        views.StoreClusterIndexView.as_view(),
        name='store-cluster-index'
    ),
    path(
        'api/clusters/create/',
        views.StoreClusterCreateView.as_view(),
        name='store-cluster-create'
    ),
    path(
        'api/clusters/<int:reg_no>/',
        views.StoreClusterView.as_view(),
        name='store-cluster-view'
    )
]