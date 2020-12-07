# SRAM iRODS integration via SAML

## Enrollment

At a certain moment the CO admin of a collaboration invites a new member to the team.
This is mainly standard SRAM functionlity.
The extra add-on for iRODS integration is the SYNC that is running close to the iRODS infrastructure and frequently inspects the SRAM LDAP for any collaboration changes.

This diagram shows what happens.

---

```plantuml
Actor Admin #Red
Actor User #Blue
Collections SRAM #Orange
database LDAP #Orange
Control SYNC #Yellow
Collections iRODS #Orange
database iCAT #Orange
Collections SSH #Orange

Admin -> SRAM: Create invitation for new user
SRAM -> User: Invitation
User -> SRAM : User completes enrollment\nuploads his SSH Public Key
SRAM -> LDAP : User is registered
LDAP -> SYNC : People/Groups/Memberships
SYNC -> iRODS : Users/Groups/Memberships
iRODS -> iCAT : iCAT is updated
SYNC -> SSH : Creates/Deletes user account\nenable SSH PublicKey logon
```

---

<!-- pagebreak -->

## Daily routine...

Once the user has been enrolled to the collaboration, he can make use of the service. The normal flow looks like this.

---

```plantuml
Actor User #Blue
Collections SSH #Orange
Collections iRODS #Orange
Control pam_web_sso #Red
Collections SRAM #Orange

User -> SSH : Open session at SSH Host
SSH -> iRODS : User initiates i-command
iRODS -> pam_web_sso : Pam module is activated
User <-- pam_web_sso : SRAM Logon link is presented
User -> SRAM : User copied link in \nbrowser and authenticates via SRAM
User <-- SRAM : PIN code is presented
User -> pam_web_sso : PIN code
pam_web_sso -> iRODS : Success !
iRODS -> User : At your service ...
```

---

During every iRODS interaction, iRODS is constantly invoking the PAM module to verify that the user still has a valid session.

The pam module is inspecting the session file in the user home directory for that. If the session lifetime is not exceeding, the PAM module responds positvely back to iRODS. As soon as the session lifetime is over, the user is presented with a new SRAM logon link to re-authenticate.

