#!/usr/bin/env python3
"""
Fetch PureGym member data (visits, activity) and save as JSON.
Run locally: python3 fetch-puregym.py
Output: puregym-data.json
"""

import json
import urllib.request
import urllib.parse
import ssl

AUTH_URL = "https://auth.puregym.com/connect/token"
API_BASE = "https://capi.puregym.com/api/v1"
CLIENT_AUTH = "Basic cm8uY2xpZW50Og=="  # ro.client:

EMAIL = "Ella.ripley@icloud.com"
PIN = "97966079"

ctx = ssl.create_default_context()


def post(url, data, headers):
    req = urllib.request.Request(url, data=data.encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, context=ctx) as res:
        return json.loads(res.read())


def get(url, token):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}"
    })
    with urllib.request.urlopen(req, context=ctx) as res:
        return json.loads(res.read())


def main():
    print("Authenticating with PureGym...")
    auth = post(AUTH_URL, urllib.parse.urlencode({
        "grant_type": "password",
        "username": EMAIL,
        "password": PIN,
        "scope": "pgcapi offline_access"
    }), {
        "Authorization": CLIENT_AUTH,
        "Content-Type": "application/x-www-form-urlencoded"
    })
    token = auth["access_token"]
    print("Authenticated.")

    print("Fetching member info...")
    member = get(f"{API_BASE}/member", token)
    print(f"  Member: {member.get('firstName', '?')} {member.get('lastName', '?')}")

    print("Fetching activity/visits...")
    try:
        activity = get(f"{API_BASE}/member/activity", token)
    except Exception as e:
        print(f"  Activity fetch failed: {e}")
        activity = None

    attendance = None
    home_gym = member.get("homeGymId")
    if home_gym:
        print(f"Fetching attendance for gym {home_gym}...")
        try:
            attendance = get(f"{API_BASE}/gyms/{home_gym}/attendance", token)
        except Exception as e:
            print(f"  Attendance fetch failed: {e}")

    output = {
        "member": {
            "firstName": member.get("firstName"),
            "lastName": member.get("lastName"),
            "homeGymId": home_gym,
            "homeGymName": member.get("homeGymName")
        },
        "activity": activity,
        "attendance": attendance
    }

    with open("puregym-data.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved to puregym-data.json")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
