"""ZincBind views."""

from django.shortcuts import render
from .models import ZincSite, Pdb

def home(request):
    return render(request, "home.html", {
     "zinc_count": ZincSite.objects.count(),
     "pdb_count": Pdb.objects.exclude(title=None).count()
    })


def data(request):
    valid = Pdb.objects.exclude(title=None)
    return render(request, "data.html", {
     "pdb_with_zinc": valid.count(),
     "pdb_without_zinc": Pdb.objects.filter(title=None).count(),
    })
