# Neakasa Integration for Home Assistant 🏠

[![GitHub Release](https://img.shields.io/github/v/release/timniklas/hass-neakasa?sort=semver&style=for-the-badge&color=green)](https://github.com/timniklas/hass-neakasa/releases/)
[![GitHub Release Date](https://img.shields.io/github/release-date/timniklas/hass-neakasa?style=for-the-badge&color=green)](https://github.com/timniklas/hass-neakasa/releases/)
![GitHub Downloads (all assets, latest release)](https://img.shields.io/github/downloads/timniklas/hass-neakasa/latest/total?style=for-the-badge&label=Downloads%20latest%20Release)
![HA Analytics](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json&query=%24.neakasa.total&style=for-the-badge&label=Active%20Installations&color=red)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/timniklas/hass-neakasa?style=for-the-badge)
[![hacs](https://img.shields.io/badge/HACS-Integration-blue.svg?style=for-the-badge)](https://github.com/hacs/integration)

## Overview

The Neakasa Home Assistant Custom Integration allows you to integrate your Neakasa devices with your Home Assistant setup.

### Currently supported devices
- Neakasa M1 (Cat Litter Box)

### Currently supported features
#### Sensors:
|Sensor|Unit|Example Value|Enabled by default|
|------|-------------|------|------|
|Cat litter level|percent|80 %|yes|
|WiFi RSS|dB|-60 dB|no (debug information)|
|Last stay time|seconds|45 s|no|
|Last usage|datetime|2024-12-07 14:52|yes|
|Device status|idle / cleaning / leveling / flipover / cat_present|idle|yes|
|Cat litter state|insufficient / moderate / sufficient|sufficient|yes|
|Bin state|normal / full / missing|normal|yes|
|Cat {name}|kg|3.8|yes|

#### Binary sensors:
|Binary Sensor|Example Value|Enabled by default|
|-------------|-------------|------------------|
|Garbage can full|off|yes|

#### Buttons:
|Button|Action|Enabled by default|
|------|------|------------------|
|Clean|Cleans the litter box|yes|
|Level|Initiates the leveling process|yes|

#### Switches:
|Switch|Enabled by default|
|------|------------------|
|Kitten mode|no (rare edgecase)|
|Child lock|yes|
|Automatic cover|yes|
|Automatic leveling|yes|
|Silent mode|yes|
|Automatic recovery|no (potentialy dangerous!)|
|Unstoppable cycle|yes|

## Installation

### HACS (recommended)

This integration is available in HACS (Home Assistant Community Store).

1. Install HACS if you don't have it already
2. Open HACS in Home Assistant
3. Go to any of the sections (integrations, frontend, automation).
4. Click on the 3 dots in the top right corner.
5. Select "Custom repositories"
6. Add following URL to the repository `https://github.com/timniklas/hass-neakasa`.
7. Select Integration as category.
8. Click the "ADD" button
9. Search for "Neakasa"
10. Click the "Download" button

### Manual installation

#### from downloaded zip archive
To install this integration manually you have to download [_neakasa.zip_](https://github.com/timniklas/hass-neakasa/releases/latest/) and extract its contents to `config/custom_components/neakasa` directory:

```bash
mkdir -p custom_components/neakasa
cd custom_components/neakasa
wget https://github.com/timniklas/hacs_blitzerde/releases/latest/download/neakasa.zip
unzip neakasa.zip
rm neakasa.zip
```
restart Home Assistant.

#### Installation from git repository

with this variant, you can easily update the integration from the github repository.

##### First installation:

```bash
cd <to your Home Assistant config directory>
git clone https://github.com/timniklas/hass-neakasa
mkdir custom_components
cd custom_components
ln -s ../hass-neakasa/custom_components/neakasa/ .
```

restart Home Assistant.

##### update the existing installation:

```bash
cd <to your Home Assistant config directory>
cd hass-neakasa/
git pull
```

restart Home Assistant.


## Configuration

### Using UI

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=neakasa)

From the Home Assistant front page go to `Configuration` and then select `Devices & Services` from the list.
Use the `Add Integration` button in the bottom right to add a new integration called `Neakasa`.

## Troubleshooting Tips / Known Issues

1. When you discover  that the mobile app is starting over and over, beginning again with the login steps, then you should use this HA integration with a different account than with the app. Create a second account and use the share function in the app - simply share the device with the second account
2. powercycle the litterbox
3. reset the litterbox and reintegrate it
4. open an issue

## Help and Contribution

If you find a problem, feel free to report it and I will do my best to help you.
If you have something to contribute, your help is greatly appreciated!
If you want to add a new feature, add a pull request first so we can discuss the details.

## Disclaimer

This custom integration is not officially endorsed or supported by Neakasa.
Use it at your own risk and ensure that you comply with all relevant terms of service and privacy policies.
