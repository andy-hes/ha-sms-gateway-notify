# SMS Gateway Notify (HACS)

Home Assistant custom integration that adds SMS notify entities plus a direct send service backed by your SMS gateway API.

## Features
- Config Flow (UI setup)
- Ask for:
  - Gateway URL/IP (example: `http://192.168.200.52:8091`)
  - API key
  - Default recipient phone numbers (comma-separated)
- Setup validation uses the status endpoint, so the API key should allow both `modem_status` and `send`
- Uses Home Assistant `notify.send_message` with one gateway entity + one entity per configured recipient
- Includes a direct `sms_gateway_notify.send_sms` service for ad-hoc numbers
- Creates a diagnostic device/sensor for gateway status

## Install via HACS (custom repository)

1. In Home Assistant -> HACS -> Integrations -> top-right menu -> Custom repositories.
2. Add repo URL and category **Integration**.
3. Install **SMS Gateway Notify**.
4. Restart Home Assistant.
5. Add integration in Settings -> Devices & Services.

## Usage
After setup, use `notify.send_message` for saved SMS entities, or `sms_gateway_notify.send_sms` for free-form numbers.

Send to the gateway default recipients:
```yaml
action:
  - service: notify.send_message
    target:
      entity_id: notify.sms_gateway_notify_gateway
    data:
      message: "Varsel fra Home Assistant"
```

Send to a specific number entity:
```yaml
action:
  - service: notify.send_message
    target:
      entity_id: notify.sms_gateway_notify_40038021
    data:
      message: "Kun til denne mottakeren"
```

Send to an ad-hoc number list:
```yaml
action:
  - service: sms_gateway_notify.send_sms
    data:
      number: "41234567"
      message: "Til valgfritt nummer"
```

Or multiple numbers:
```yaml
action:
  - service: sms_gateway_notify.send_sms
    data:
      numbers: "41234567, 40038021"
      message: "Til valgfritt nummer"
```

If you add more phone numbers in the integration options, new notify entities are created for them.

If you change IP, API key, or recipients later, use the integration options (gear icon) to edit them.

## Requirements on gateway side
- Endpoint: `POST /api/external/send`
- Header: `X-API-Key`
- JSON payload: `{ "number": "40038021", "text": "..." }`
- API key must include `send` scope.
- Setup validation calls `/api/external/status`, so key should also include `modem_status` scope.

## Notes
- Phone number validation is done by gateway API.
- Saved notify entities use configured recipients.
- The direct `sms_gateway_notify.send_sms` service is for ad-hoc numbers.
