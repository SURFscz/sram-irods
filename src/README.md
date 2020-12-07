# SRAM iRODS integration via SAML

@startuml
Actor Admin #Red
Actor User #Blue
Collections SRAM #Orange
database LDAP #Orange
Control SYNC #Yellow
Collections iRODS #Orange
database iCAT #Orange
Collections SSH #Orange
Control pam_web_sso #Red

Admin -> SRAM: Create invitation for new user
SRAM -> User: Invitation
User -> SRAM : User completes enrollment\nuploads his SSH Public Key
SRAM -> LDAP : User is registered
LDAP -> SYNC : People/Groups/Memberships
SYNC -> iRODS : Users/Groups/Memberships
iRODS -> iCAT : iCAT is updated
SYNC -> SSH : Creates/Deletes user account\nenable SSH PublicKey logon
User -> SSH : Open session at SSH Host
SSH -> iRODS : User initiates i-command
iRODS -> pam_web_sso : Pam module is activated to authenticate user
pam_web_sso -> User : Show SRAM Logon link
User -> SRAM : User copied link in \nbrowser and authenticates via SRAM\nuser gets PIN code on success
User -> pam_web_sso : User enter PIN code
pam_web_sso -> iRODS : Success !
iRODS -> User : At your service ...
@enduml
