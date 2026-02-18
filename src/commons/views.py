from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from src.services.user.models import UserProfile, PendingReferral
from src.commons.utils import get_client_ip


class PasswordResetConfirmPageView(View):
    """
    Renders a branded HTML page for password reset.
    Validates the token on load — shows error state if invalid/expired.
    """
    def get(self, request, uidb64, token):
        from allauth.account.utils import url_str_to_user_pk
        from allauth.account.forms import default_token_generator
        from django.contrib.auth import get_user_model
        User = get_user_model()

        valid = False
        try:
            uid = url_str_to_user_pk(uidb64)
            user = User.objects.get(pk=uid)
            valid = default_token_generator.check_token(user, token)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            valid = False

        return render(request, 'password_reset_confirm.html', {
            'uid': uidb64,
            'token': token,
            'valid': valid,
        })


class EmailConfirmPageView(View):
    """
    Renders a branded HTML page for email verification.
    Validates the key on load — shows error if invalid/already confirmed.
    """
    def get(self, request, key):
        from allauth.account.models import EmailConfirmationHMAC, EmailConfirmation

        valid = False
        email = None
        try:
            # Try HMAC-based confirmation first (default in modern allauth)
            confirmation = EmailConfirmationHMAC.from_key(key)
            if confirmation:
                email = confirmation.email_address.email
                valid = True
            else:
                # Fall back to DB-based confirmation
                confirmation = EmailConfirmation.objects.get(key=key)
                if not confirmation.key_expired():
                    email = confirmation.email_address.email
                    valid = True
        except (EmailConfirmation.DoesNotExist, Exception):
            valid = False

        return render(request, 'email_confirm.html', {
            'key': key,
            'valid': valid,
            'email': email,
        })


@method_decorator(csrf_exempt, name='dispatch')
class DownloadPageView(View):
	"""
	Simple download landing page.

	GET /download/?refcode=ABC123  - shows the download page and referrer info (if present)
	POST /download/ - records a click (body must include 'refcode') and stores IP+refcode
	"""

	def get(self, request):
		refcode = request.GET.get('refcode') or None
		context = {
			'referral_code': refcode,
			'google_play_url': 'https://play.google.com/store/apps/details?id=com.yourapp',
			'app_store_url': 'https://apps.apple.com/app/idYOURAPPID',
		}

		if refcode:
			try:
				profile = UserProfile.objects.get(referral_code=refcode.upper())
				context['referrer_username'] = profile.user.username
				context['valid_code'] = True
			except UserProfile.DoesNotExist:
				context['valid_code'] = False

		return render(request, 'download.html', context)

	def post(self, request):
		# Expect JSON body with { "refcode": "ABC123", "store": "google_play" }
		try:
			import json
			body = json.loads(request.body.decode() or '{}')
		except Exception as e:
			import logging
			logger = logging.getLogger(__name__)
			logger.warning(f"DownloadPageView POST: Failed to parse JSON body: {e}")
			body = {}

		refcode = (body.get('refcode') or request.GET.get('refcode'))
		if not refcode:
			return JsonResponse({'success': False, 'error': 'missing refcode'}, status=400)

		# Validate referral code exists — avoid storing bogus codes; still prefer IP attribution later
		try:
			profile = UserProfile.objects.get(referral_code=refcode.upper())
		except UserProfile.DoesNotExist:
			return JsonResponse({'success': False, 'error': 'invalid refcode'}, status=400)

		client_ip = get_client_ip(request)
		if not client_ip:
			return JsonResponse({'success': False, 'error': 'could not determine ip'}, status=400)

		# Avoid duplicate unredeemed entries for same ip+referrer_profile
		existing = PendingReferral.objects.filter(
			referrer_profile=profile,
			ip_address=client_ip,
			redeemed_at__isnull=True
		).first()
		if existing:
			return JsonResponse({'success': True, 'tracked': False, 'already_exists': True})

		# Create the pending referral with FK to the referrer profile
		try:
			PendingReferral.objects.create(
				referral_code=refcode.upper(),
				referrer_profile=profile,
				ip_address=client_ip
			)
			return JsonResponse({'success': True, 'tracked': True})
		except Exception as e:
			import logging
			logger = logging.getLogger(__name__)
			logger.error(f"DownloadPageView POST: Failed to create PendingReferral: {e}")
			return JsonResponse({'success': False, 'error': 'failed to track click'}, status=500)
