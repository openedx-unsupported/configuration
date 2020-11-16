# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] 2020-02-28

## [0.2.2-i.2] - 2020-02-26

### Changed

- Support email is changed to skillsnetwork email but set inside the run.yml file instead of build.yml

## [0.2.1-i.2] - 2020-02-25

### Changed

- Support email is now skillsnetwork email not example email

## [0.5.1-e.2] - 2019-03-01

### Added

- Custom favicon URL

### Fixed

- Fixed /portal endpoint to not require a `/` at the end

## [0.5.0-e.2] - 2017-09-15

### Added

- Enable LMS Preview

### Changed

- Point `lms`, `lms-preview` and `cms` to `load-balancer`

## [0.4.1-e.2] - 2017-06-08

### Changed

- Fixed portal location regex in lms

## [0.4.0-e.2] - 2017-04-18

### Changed

- Add route to redirect URL to Portal
- Render nginx configuration files at run time

## [0.3.2-e.2] - 2017-03-20
### Changed
- Fix `cms` upstream hostname for Rancher 1.4.1

## [0.3.1-e.2] - 2017-03-18

### Changed

- Revert `NGINX_SET_X_FORWARDED_HEADERS` to `False` since it breaks Oauth

## [0.3.0-e.2] - 2017-03-16

### Added

- Log to `STDOUT` and `STDERR`

## [0.2.1-e.2] - 2017-03-16

### Changed

- Set `NGINX_SET_X_FORWARDED_HEADERS` to `True`
- Use `lms-load-balancer` as LMS host
