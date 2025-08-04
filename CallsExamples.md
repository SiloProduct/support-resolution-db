
# get filter tickets (fetching all ids)
## Request
curl --location 'https://heysilo-help.freshdesk.com//api/v2/search/tickets?query=%22status%3A4%20OR%20status%3A5%22&page=3' \
--header 'Authorization: Basic TmZtbnh5Tm9ReENBQ1RpSHRzcUY6WA==' \
--data ''


## Example response
{
    "results": [
        {
            "cc_emails": [
                "kjl@alumni.utexas.net"
            ],
            "fwd_emails": [],
            "reply_cc_emails": [
                "kjl@alumni.utexas.net"
            ],
            "ticket_cc_emails": [],
            "ticket_bcc_emails": [],
            "fr_escalated": true,
            "spam": false,
            "email_config_id": 501000072656,
            "group_id": 501000283279,
            "priority": 1,
            "requester_id": 501005124643,
            "responder_id": 501003979303,
            "source": 7,
            "company_id": null,
            "status": 5,
            "subject": "Wi-Fi setup issue",
            "association_type": null,
            "support_email": null,
            "to_emails": null,
            "product_id": 501000065697,
            "id": 169,
            "type": "Problem",
            "due_by": "2025-07-31T19:45:08Z",
            "fr_due_by": "2025-07-25T18:24:46Z",
            "is_escalated": false,
            "description": "<div>This customer has experienced issues connecting their device to their Wi-Fi network and requires assistance</div>",
            "description_text": "This customer has experienced issues connecting their device to their Wi-Fi network and requires assistance",
            "custom_fields": {
                "cf_device_serial": "GP392W2250800325",
                "cf_serial_number": null,
                "cf_deviceid": null,
                "cf_groupid": null
            },
            "created_at": "2025-07-24T18:24:46Z",
            "updated_at": "2025-08-02T10:59:26Z",
            "associated_tickets_count": null,
            "tags": [
                "Wi-Fi issue"
            ],
            "structured_description": null
        },
        {
            "cc_emails": [
                "info@heysilo.com"
            ],
            "fwd_emails": [],
            "reply_cc_emails": [
                "info@heysilo.com"
            ],
            "ticket_cc_emails": [
                "info@heysilo.com"
            ],
            "ticket_bcc_emails": [],
            "fr_escalated": false,
            "spam": false,
            "email_config_id": 501000072656,
            "group_id": null,
            "priority": 1,
            "requester_id": 501004824041,
            "responder_id": null,
            "source": 1,
            "company_id": null,
            "status": 5,
            "subject": "Fwd: SILO-EB8-BK-RM",
            "association_type": null,
            "support_email": "heysilocomsupport@heysilo-help.freshdesk.com",
            "to_emails": [
                "support@heysilo.com"
            ],
            "product_id": 501000065697,
            "id": 167,
            "type": "Problem",
            "due_by": "2025-07-29T15:08:04Z",
            "fr_due_by": "2025-07-25T15:08:04Z",
            "is_escalated": false,
            "description": "<div>---------- Forwarded message ---------<br>From: Daniel Ryan &lt;Daniel.Ryan@fkabrands.com&gt;<br>Date: Thu, 24 Jul 2025 15:07:31 +0000<br>Subject: SILO-EB8-BK-RM<br>To: Hey Silo &lt;info@heysilo.com&gt;<br><br>&lt;&lt;ZAPPED&gt;&gt;<br>The below consumer contacted us by phone for support. Please reach out to them.<br><br>Name: John Lovaglio<br>Phone: (757) 675-9350<br>Email: jlovaglio@gmail.com&lt;mailto:jlovaglio@gmail.com&gt;<br>Address: 12532 93rd Way Largo, FL 33773<br><br>The consumer explained they were trying to connect the Silo. Unit will<br>not connect to Wi-Fi, consumer made sure it was connected to the<br>2.4ghz network.<br>\n</div>\n",
            "description_text": "---------- Forwarded message ---------\r\nFrom: Daniel Ryan <Daniel.Ryan@fkabrands.com>\r\nDate: Thu, 24 Jul 2025 15:07:31 +0000\r\nSubject: SILO-EB8-BK-RM\r\nTo: Hey Silo <info@heysilo.com>\r\n\r\n<<ZAPPED>>\r\nThe below consumer contacted us by phone for support. Please reach out to them.\r\n\r\nName: John Lovaglio\r\nPhone: (757) 675-9350\r\nEmail: jlovaglio@gmail.com<mailto:jlovaglio@gmail.com>\r\nAddress: 12532 93rd Way Largo, FL 33773\r\n\r\nThe consumer explained they were trying to connect the Silo. Unit will\r\nnot connect to Wi-Fi, consumer made sure it was connected to the\r\n2.4ghz network.\r\n",
            "custom_fields": {
                "cf_device_serial": null,
                "cf_serial_number": null,
                "cf_deviceid": null,
                "cf_groupid": null
            },
            "created_at": "2025-07-24T15:08:04Z",
            "updated_at": "2025-07-25T07:01:57Z",
            "associated_tickets_count": null,
            "tags": [],
            "structured_description": null
        },
        {
            "cc_emails": [
                "info@heysilo.com"
            ],
            "fwd_emails": [],
            "reply_cc_emails": [
                "info@heysilo.com"
            ],
            "ticket_cc_emails": [
                "info@heysilo.com"
            ],
            "ticket_bcc_emails": [],
            "fr_escalated": false,
            "spam": false,
            "email_config_id": 501000072656,
            "group_id": 501000283278,
            "priority": 1,
            "requester_id": 501005073089,
            "responder_id": 501004184540,
            "source": 1,
            "company_id": null,
            "status": 5,
            "subject": "Fwd:",
            "association_type": null,
            "support_email": "heysilocomsupport@heysilo-help.freshdesk.com",
            "to_emails": [
                "support@heysilo.com"
            ],
            "product_id": 501000065697,
            "id": 166,
            "type": "Shipping",
            "due_by": "2025-08-03T02:54:58Z",
            "fr_due_by": "2025-07-25T02:33:42Z",
            "is_escalated": false,
            "description": "<div>---------- Forwarded message ---------<br>From: Erica Porter &lt;ericaporter@gmail.com&gt;<br>Date: Wed, 23 Jul 2025 20:31:16 -0600<br>Subject:<br>To: Hey Silo &lt;info@heysilo.com&gt;<br><br>&lt;&lt;ZAPPED&gt;&gt;<br>I still have not received my silo or even a final details to shipment on<br>the product, what do I need to do??<br><br>*Erica Porter*<br>&lt;<a href=\"http://www.ericascottphotography.com\" rel=\"noreferrer\">http://www.ericascottphotography.com</a>&gt;<br>* &lt;<a href=\"http://www.ericascottphotography.com&gt;*\" rel=\"noreferrer\">http://www.ericascottphotography.com&gt;*</a><br><br>*<a href=\"http://www.ericascottphotography.com\" rel=\"noreferrer\">www.ericascottphotography.com</a><br>&lt;<a href=\"http://www.ericascottphotography.com&gt;ericaporter@gmail.com\" rel=\"noreferrer\">http://www.ericascottphotography.com&gt;ericaporter@gmail.com</a><br>&lt;ericaporter@gmail.com&gt;*<br>\n</div>\n",
            "description_text": "---------- Forwarded message ---------\r\nFrom: Erica Porter <ericaporter@gmail.com>\r\nDate: Wed, 23 Jul 2025 20:31:16 -0600\r\nSubject:\r\nTo: Hey Silo <info@heysilo.com>\r\n\r\n<<ZAPPED>>\r\nI still have not received my silo or even a final details to shipment on\r\nthe product, what do I need to do??\r\n\r\n*Erica Porter*\r\n<http://www.ericascottphotography.com>\r\n* <http://www.ericascottphotography.com>*\r\n\r\n*www.ericascottphotography.com\r\n<http://www.ericascottphotography.com>ericaporter@gmail.com\r\n<ericaporter@gmail.com>*\r\n",
            "custom_fields": {
                "cf_device_serial": null,
                "cf_serial_number": null,
                "cf_deviceid": null,
                "cf_groupid": null
            },
            "created_at": "2025-07-24T02:33:42Z",
            "updated_at": "2025-07-29T18:59:25Z",
            "associated_tickets_count": null,
            "tags": [],
            "structured_description": null
        },...
    ],
    "total": 133
}





# get ticket conversation
## request
curl --location --globoff 'https://heysilo-help.freshdesk.com/api/v2/tickets/{{ticketId}}?include=conversations' \
--header 'Authorization: Basic TmZtbnh5Tm9ReENBQ1RpSHRzcUY6WA==' \
--data ''

## Example response 
{
    "cc_emails": [],
    "fwd_emails": [],
    "reply_cc_emails": [],
    "ticket_cc_emails": [],
    "ticket_bcc_emails": [],
    "fr_escalated": true,
    "spam": false,
    "email_config_id": 501000072585,
    "group_id": 501000283279,
    "priority": 1,
    "requester_id": 501005088825,
    "responder_id": 501003979303,
    "source": 10,
    "company_id": null,
    "status": 9,
    "subject": "Silo WiFi Setup Troubleshooting",
    "association_type": null,
    "support_email": "support@heysilo-help.freshdesk.com",
    "to_emails": [
        "support@heysilo-help.freshdesk.com"
    ],
    "product_id": 501000065697,
    "id": 223,
    "type": "Problem",
    "due_by": "2025-07-31T16:27:29Z",
    "fr_due_by": "2025-07-27T16:27:29Z",
    "is_escalated": true,
    "description": "...",
    "description_text": "Hi there,  Thanks for reaching out and letting us know you’re having trouble connecting your Silo to Wi-Fi. We want to get you up and running as smoothly as possible!  To help us pinpoint the issue, could you let us know at which step you’re getting stuck during the setup? If you’re seeing any error messages, please share what they say.  One common issue is if your Wi-Fi network name or password includes spaces or special characters. If that’s the case, your Silo may need a quick software update to support these types of networks. There’s a simple workaround: you can connect your Silo to a temporary network just long enough to complete the update. We’ve put together a step-by-step Temporary Network Setup Guide to walk you through this process:  Setting up Silo using a temporary network  Once you let us know more details about where things are getting stuck, we’ll guide you through the next steps. Looking forward to your reply!  In Freshness?,  The Silo Support Team",
    "custom_fields": {
        "cf_device_serial": null,
        "cf_serial_number": null,
        "cf_deviceid": null,
        "cf_groupid": null
    },
    "created_at": "2025-07-25T07:01:06Z",
    "updated_at": "2025-08-03T12:53:53Z",
    "tags": [
        "Device issue"
    ],
    "attachments": [],
    "source_additional_info": null,
    "structured_description": null,
    "conversations": [
        {
            "body": "...",
            "body_text": "Tickets with IDs 167 is merged into this ticket.",
            "structured_body": null,
            "id": 501012837977,
            "incoming": false,
            "private": true,
            "user_id": 501003979303,
            "support_email": "support@heysilo-help.freshdesk.com",
            "source": 2,
            "category": 2,
            "to_emails": [],
            "from_email": "support@heysilo-help.freshdesk.com",
            "cc_emails": [],
            "bcc_emails": null,
            "email_failure_count": null,
            "outgoing_failures": null,
            "thread_id": null,
            "thread_message_id": null,
            "created_at": "2025-07-25T07:01:57Z",
            "updated_at": "2025-07-25T07:01:57Z",
            "last_edited_at": null,
            "last_edited_user_id": null,
            "attachments": [],
            "automation_id": null,
            "automation_type_id": null,
            "auto_response": false,
            "ticket_id": 223,
            "threading_type": null,
            "delivery_details": {
                "failed_emails": [],
                "pending_emails": []
            },
            "source_additional_info": null
        },
        {
            "body": "...",
            "body_text": "Merged from ticket 167  \n      Subject: Fwd: SILO-EB8-BK-RM  \n      Description:  ---------- Forwarded message --------- From: Daniel Ryan <Daniel.Ryan@fkabrands.com> Date: Thu, 24 Jul 2025 15:07:31 +0000 Subject: SILO-EB8-BK-RM To: Hey Silo <info@heysilo.com>  <<ZAPPED>> The below consumer contacted us by phone for support. Please reach out to them.  Name: John Lovaglio Phone: (757) 675-9350 Email: jlovaglio@gmail.com<mailto:jlovaglio@gmail.com> Address: 12532 93rd Way Largo, FL 33773  The consumer explained they were trying to connect the Silo. Unit will not connect to Wi-Fi, consumer made sure it was connected to the 2.4ghz network.",
            "structured_body": null,
            "id": 501012837978,
            "incoming": false,
            "private": true,
            "user_id": 501003979303,
            "support_email": null,
            "source": 2,
            "category": 2,
            "to_emails": [],
            "from_email": null,
            "cc_emails": [],
            "bcc_emails": null,
            "email_failure_count": null,
            "outgoing_failures": null,
            "thread_id": null,
            "thread_message_id": null,
            "created_at": "2025-07-25T07:01:57Z",
            "updated_at": "2025-07-25T07:01:57Z",
            "last_edited_at": null,
            "last_edited_user_id": null,
            "attachments": [],
            "automation_id": null,
            "automation_type_id": null,
            "auto_response": false,
            "ticket_id": 223,
            "threading_type": null,
            "delivery_details": {
                "failed_emails": [],
                "pending_emails": []
            },
            "source_additional_info": null
        },
        {
            "body": "...",
            "body_text": "So  I did all that and it said connected to WiFi,  then it said to log in\r\nso I logged in and it just got stuck on \"Please log in to Silo\" even if I\r\nam logged in.  I also asked for a phone call and nobody called me!\r\n\r\nOn Fri, Jul 25, 2025 at 3:01 AM Silo support <\r\nsupport@heysilo-help.freshdesk.com> wrote:\r\n\r\n> Hi there,\r\n> Thanks for reaching out and letting us know you’re having trouble\r\n> connecting your Silo to Wi-Fi. We want to get you up and running as\r\n> smoothly as possible!\r\n> To help us pinpoint the issue, could you let us know at which step you’re\r\n> getting stuck during the setup? If you’re seeing any error messages, please\r\n> share what they say.\r\n> One common issue is if your Wi-Fi network name or password includes spaces\r\n> or special characters. If that’s the case, your Silo may need a quick\r\n> software update to support these types of networks. There’s a simple\r\n> workaround: you can connect your Silo to a temporary network just long\r\n> enough to complete the update. We’ve put together a step-by-step Temporary\r\n> Network Setup Guide to walk you through this process:\r\n> Setting up Silo using a temporary network\r\n> <https://www.heysilo.com/a/support-portal/technical-support-troubleshooting/setting-up-silo-using-a-temporary-network>\r\n> Once you let us know more details about where things are getting stuck,\r\n> we’ll guide you through the next steps. Looking forward to your reply!\r\n> In Freshness?,\r\n> The Silo Support Team\r\n>\r\n> 223:4317325\r\n>\r\n\r\n",
            "structured_body": null,
            "id": 501013389717,
            "incoming": true,
            "private": false,
            "user_id": 501005088825,
            "support_email": "jlovaglio@gmail.com",
            "source": 0,
            "category": 1,
            "to_emails": [
                "\"Silo support\" <support@heysilo-help.freshdesk.com>"
            ],
            "from_email": "jlovaglio@gmail.com",
            "cc_emails": [],
            "bcc_emails": [],
            "email_failure_count": null,
            "outgoing_failures": null,
            "thread_id": null,
            "thread_message_id": null,
            "created_at": "2025-07-26T16:27:29Z",
            "updated_at": "2025-07-26T16:27:29Z",
            "last_edited_at": null,
            "last_edited_user_id": null,
            "attachments": [],
            "automation_id": null,
            "automation_type_id": null,
            "auto_response": false,
            "ticket_id": 223,
            "threading_type": null,
            "delivery_details": {
                "failed_emails": [],
                "pending_emails": []
            },
            "source_additional_info": null
        },...
    ]
}

