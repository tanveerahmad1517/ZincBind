from collections import Counter
from django.shortcuts import render
from django.db.models import F
from django.http import HttpResponse
from django.core.management import call_command
from zinc.models import ZincSite, Pdb, Residue, ZincSiteCluster
from zinc.views import search

def home(request):
    """Returns the home page, along with some object counts."""

    return render(request, "home.html", {"counts": [
     ZincSiteCluster.objects.count(),
     ZincSite.objects.count(),
     Pdb.objects.count()
    ]})


def changelog(request):
    """Returns the changelog page."""

    return render(request, "changelog.html")


def about(request):
    """Returns the about page."""

    return render(request, "about.html")


def help(request):
    """Returns the help page."""

    return render(request, "help.html")


def data(request):
    """Returns the data page and the relevant values needed for its charts."""

    if request.method == "POST":
        with open(
         "data/zinc." + request.POST["datatype"],
         "r" + ("b" if request.POST["datatype"] == "sqlite3" else "")
        ) as f:
            filebody = f.read()
        response = HttpResponse(
         filebody, content_type="application/plain-text"
        )
        response["Content-Disposition"] = 'attachment; filename="zinc.{}"'.format(
         request.POST["datatype"]
        )
        return response
    residue_counts = Residue.name_counts(5)
    sites = ZincSite.objects.all().annotate(
     organism=F("pdb__organism"),
     classification=F("pdb__classification"),
     technique=F("pdb__technique"),
     resolution=F("pdb__resolution")
    )
    technique_counts = ZincSite.property_counts(sites, "technique", 3)
    species_counts = ZincSite.property_counts(sites, "organism", 6)
    class_counts = ZincSite.property_counts(sites, "classification", 6)
    code_counts = ZincSite.property_counts(sites, "code", 9, unique=True)
    resolutions = [["<1.5Å ", "1.5-2.0Å", "2.0-2.5Å", "2.5-3.0Å", "3.0Å+", "None"], [
     sites.filter(resolution__lt=1.5).count(),
     sites.filter(resolution__lt=2.0, resolution__gte=1.5).count(),
     sites.filter(resolution__lt=2.5, resolution__gte=2.0).count(),
     sites.filter(resolution__lt=3.0, resolution__gte=2.5).count(),
     sites.filter(resolution__gte=3.0).count(),
     sites.filter(resolution=None).count(),
    ]]
    return render(request, "data.html", {
     "bar_data": [residue_counts, technique_counts, species_counts, class_counts, code_counts, resolutions]
    })


def all_data(request):
    request.GET = request.GET.copy()
    request.GET["q"] = " "
    return search(request)
