"""HTML presentation views for the Landlord Verification workflow (Phase 3).

This presents the landlord-side verification submission page (AGENTS 9, 42):
a landlord submits their verification information, and the page shows the
current status of their submission. The submission is an *administrative
platform control* - it does not legally verify ownership or land title, and the
UI is careful to say so (AGENTS 9, 17).
"""
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views import View

from .models import VerificationRequest

User = get_user_model()


class VerificationRequestForm(forms.ModelForm):
    """Landlord's verification submission form.

    The landlord supplies information about themselves and their properties so
    an administrator can review the account. ``status`` and ``remarks`` are
    administrative outcomes and are never editable here.
    """

    class Meta:
        model = VerificationRequest
        fields = ["information"]
        labels = {
            "information": (
                "Verification information (e.g. your property details and "
                "contact information for the administrator review)"
            )
        }
        widgets = {
            "information": forms.Textarea(
                attrs={"class": "form-control", "rows": 6}
            )
        }


class LandlordVerificationView(LoginRequiredMixin, View):
    """Landlord-only page to submit or review their verification request.

    A landlord may have at most one request per review cycle; submitting again
    creates a fresh pending request reusing the latest information.
    """

    template_name = "verification/form.html"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (user and user.is_authenticated and (user.is_landlord or user.is_admin)):
            return HttpResponseForbidden("Forbidden")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        request_obj = VerificationRequest.objects.filter(
            landlord=request.user
        ).first()
        form = VerificationRequestForm(
            instance=request_obj if request_obj else None
        )
        return render(
            request,
            self.template_name,
            {"form": form, "request_obj": request_obj},
        )

    def post(self, request):
        form = VerificationRequestForm(request.POST)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.landlord = request.user
            verification.status = VerificationRequest.Status.PENDING
            verification.reviewed_by = None
            verification.reviewed_at = None
            verification.remarks = ""
            verification.save()
            messages.success(
                request,
                "Your verification information has been submitted for "
                "administrative review.",
            )
            return redirect("verification-form")
        return render(
            request,
            self.template_name,
            {"form": form, "request_obj": None},
            status=400,
        )