# Add JWT Refresh Token Support

## Summary

This pull request introduces JWT refresh token support to improve the user authentication experience by allowing access tokens to be renewed without requiring users to log in again.

## Changes

- Added `/api/auth/refresh` endpoint
- Updated authentication middleware
- Added refresh token validation
- Added Redis support for token revocation
- Refactored AuthService authentication flow

## Motivation

Currently users must authenticate again whenever an access token expires. This change allows clients to exchange a refresh token for a new access token.

## Risk

Medium

Authentication is a critical component of the platform. Any defects could impact user logins and session management.

## Testing

- Manual API testing completed
- Existing authentication regression suite passed

## Rollback Plan

Revert this pull request.