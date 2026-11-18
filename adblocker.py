import re
from urllib.parse import urlparse

# Comprehensive database of ad networks, telemetry trackers, and ad exchanges
BUILTIN_AD_DOMAINS = {
    # Google Ad Services & DoubleClick
    "doubleclick.net", "googleadservices.com", "googlesyndication.com",
    "adservice.google.com", "pagead2.googlesyndication.com", "admob.com",
    "fundingchoicesmessages.google.com", "securepubads.g.doubleclick.net",
    "tpc.googlesyndication.com", "ad.doubleclick.net", "static.doubleclick.net",
    "googleads.g.doubleclick.net", "pubads.g.doubleclick.net",
    "ads.youtube.com", "googletagservices.com", "googletagmanager.com",

    # Major Ad Networks & Header Bidders
    "criteo.com", "criteo.net", "static.criteo.net", "bidder.criteo.com",
    "taboola.com", "cdn.taboola.com", "trc.taboola.com",
    "outbrain.com", "widgets.outbrain.com", "log.outbrain.com",
    "adnxs.com", "ib.adnxs.com", "secure.adnxs.com",
    "rubiconproject.com", "fastlane.rubiconproject.com",
    "openx.net", "pubmatic.com", "ads.pubmatic.com",
    "casalemedia.com", "smartadserver.com", "adroll.com", "advertising.com",
    "yieldmo.com", "triplelift.com", "media.net", "revcontent.com",
    "infolinks.com", "popads.net", "popcash.net", "propellerads.com",
    "adsterra.com", "exoclick.com", "trafficjunky.com", "mgid.com",
    "adblade.com", "adcolony.com", "chartboost.com", "unityads.unity3d.com",
    "applovin.com", "ironsrc.com", "vungle.com", "fyber.com",
    "bidswitch.net", "sonobi.com", "conversantmedia.com", "sovrn.com",
    "gumgum.com", "sharethrough.com", "teads.tv", "undertone.com",
    "amazon-adsystem.com", "a-mo.net", "adform.net", "spotxchange.com",
    "moatads.com", "adtechus.com", "quantcount.com",

    # Trackers, Analytics & Fingerprinters
    "google-analytics.com", "analytics.google.com", "hotjar.com",
    "mouseflow.com", "crazyegg.com", "fullstory.com", "segment.io",
    "segment.com", "mixpanel.com", "amplitude.com", "heapanalytics.com",
    "scorecardresearch.com", "quantserve.com", "statcounter.com",
    "histats.com", "clicky.com", "mc.yandex.ru", "clarity.ms",
    "newrelic.com", "nr-data.net", "bugsnag.com", "sentry.io",
    "datadoghq.com", "inspectlet.com",

    # Social Trackers & Pixels
    "connect.facebook.net", "pixel.facebook.com", "analytics.twitter.com",
    "static.ads-twitter.com", "ads-twitter.com", "tr.snapchat.com",
    "sc-static.net", "analytics.tiktok.com", "ads.tiktok.com",
    "tr.pinterest.com", "pixel.wp.com", "redditstatic.com/ads",

    # Crypto Miners & Malvertising
    "coinhive.com", "coin-have.com", "cryptoloot.pro", "jsecoin.com",
    "webminepool.com", "minr.pw", "authedmine.com", "crypto-loot.com",

    # Telemetry
    "vortex.data.microsoft.com", "telemetry.microsoft.com",
    "browser.pipe.aria.microsoft.com", "telemetry.nvidia.com"
}

AD_KEYWORDS = [
    "doubleclick", "googlesyndication", "googleadservices", "googleads",
    "/pagead/", "/adservice", "amazon-adsystem", "adnxs", "criteo",
    "taboola", "outbrain", "rubiconproject", "pubmatic", "adsystem",
    "adserver", "/ads/", "/ad/", "popunder", "popads", "propellerads",
    "adsterra", "exoclick", "adcolony", "applovin", "unityads",
    "google-analytics", "hotjar", "coinhive"
]

COSMETIC_AD_BLOCK_CSS = """
/* IMPERIAL REV-LAUNCHER DEFENSIVE AD VAPORIZER */
.adsbygoogle,
.ad-container,
.ad-box,
.ad-wrapper,
.ad-unit,
.ad-slot,
.ad-banner,
.advertisement,
.advert,
.sponsor-banner,
.sponsored-post,
[id^="ad_"],
[id^="google_ads"],
[id*="ScriptRoot"],
[class*="sponsored"],
[class*="advertisement"],
[class*="ad-banner"],
[aria-label="advertisement" i],
[aria-label="sponsored" i],
iframe[src*="doubleclick.net"],
iframe[src*="adnxs.com"],
iframe[src*="googlesyndication.com"],
iframe[id*="google_ads_frame"],
div[data-ad-unit],
div[data-ad-client],
div[data-google-query-id],
.ytd-ad-slot-renderer,
.ytd-in-feed-ad-layout-renderer,
.ytd-banner-promo-renderer-background,
.ytd-player-legacy-desktop-watch-ads-renderer,
#masthead-ad,
ytd-ad-slot-renderer {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
}
"""

class ImperialAdBlocker:
    def __init__(self):
        self.enabled = True
        self.blocked_domains = set(BUILTIN_AD_DOMAINS)
        self.custom_blocked = set()
        self.whitelisted_domains = set()

        # Telemetry metrics
        self.total_blocked = 0
        self.ads_blocked = 0
        self.trackers_blocked = 0
        self.malware_blocked = 0
        self.bytes_saved = 0

    def should_block(self, url_str: str) -> bool:
        if not self.enabled:
            return False

        try:
            url_lower = url_str.lower()

            # YouTube ad endpoints
            if "youtube.com/pagead" in url_lower or "youtube.com/api/stats/ads" in url_lower:
                self._record_block(url_str, is_tracker=False)
                return True

            parsed = urlparse(url_lower)
            hostname = parsed.hostname
            if not hostname:
                return False

            # Check whitelist
            for white in self.whitelisted_domains:
                if hostname == white or hostname.endswith("." + white):
                    return False

            # Check exact or suffix domain
            for blocked in self.blocked_domains:
                if hostname == blocked or hostname.endswith("." + blocked):
                    self._record_block(url_str, is_tracker="analytics" in hostname or "tracker" in hostname or "pixel" in hostname)
                    return True

            for custom in self.custom_blocked:
                if hostname == custom or hostname.endswith("." + custom):
                    self._record_block(url_str, is_tracker=False)
                    return True

            # Keyword matching on full URL
            for kw in AD_KEYWORDS:
                if kw in url_lower:
                    self._record_block(url_str, is_tracker="analytics" in kw)
                    return True

        except Exception:
            return False

        return False

    def _record_block(self, url: str, is_tracker: bool = False):
        self.total_blocked += 1
        if is_tracker:
            self.trackers_blocked += 1
        else:
            self.ads_blocked += 1
        self.bytes_saved += 160 * 1024

    def add_custom_rule(self, domain: str):
        cleaned = domain.strip().lower()
        if cleaned:
            self.custom_blocked.add(cleaned)

    def add_whitelist(self, domain: str):
        cleaned = domain.strip().lower()
        if cleaned:
            self.whitelisted_domains.add(cleaned)

    def get_cosmetic_css(self) -> str:
        return COSMETIC_AD_BLOCK_CSS

    def get_stats(self):
        saved_mb = self.bytes_saved / (1024 * 1024)
        return {
            "total_blocked": self.total_blocked,
            "ads_blocked": self.ads_blocked,
            "trackers_blocked": self.trackers_blocked,
            "malware_blocked": self.malware_blocked,
            "mb_saved": round(saved_mb, 2)
        }

adblocker = ImperialAdBlocker()
