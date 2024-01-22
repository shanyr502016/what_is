Dita Module Commands:
=====================================================================
Clearlocks:
    ./dita_deploy.sh -m Clearlocks -p $PACKAGEID
---------------------------------------------------------------------
    ./dita_deploy.sh -m Clearlocks.verbose -p $PACKAGEID
---------------------------------------------------------------------
    ./dita_deploy.sh -m Clearlocks.assertAllDead -p $PACKAGEID
=====================================================================
Preferences.Override.Site:
    ./dita_deploy.sh -m Preferences.Override.Site -p $PACKAGEID
---------------------------------------------------------------------
Preferences.Override.Group:
    ./dita_deploy.sh -m Preferences.Override.Group -p $PACKAGEID
---------------------------------------------------------------------
Preferences.Override.Role:
    ./dita_deploy.sh -m Preferences.Override.Role -p $PACKAGEID
---------------------------------------------------------------------
Preferences.Merge.Site:
    ./dita_deploy.sh -m Preferences.Merge.site -p $PACKAGEID
---------------------------------------------------------------------
Preferences:
    ./dita_deploy.sh -m Preferences -p  $PACKAGEID
=====================================================================
Organization.makeuser:
    ./dita_deploy.sh -m Organization.makeuser -p $PACKAGEID
=====================================================================
CopyLangTextServer.all:
    ./dita_deploy.sh -m CopyLangTextServer.all -p  $PACKAGEID
=====================================================================
PreBMIDE:
    ./dita_deploy.sh -m PreBMIDE -p $PACKAGEID
=====================================================================
DCScript Export Environment:
---------------------------------------------------------------------
LNX:
    ./dita_deploy.sh -m DCScript.exportENVXML.lnx -p $PACKAGEID
---------------------------------------------------------------------
WIN:
    ./dita_deploy.sh -m DCScript.exportENVXML.win -p $PACKAGEID
---------------------------------------------------------------------
DCScript Generate Deploy Scripts:
---------------------------------------------------------------------
LNX:
    ./dita_deploy.sh -m DCScript.generateDeployScripts.lnx -p $PACKAGEID
---------------------------------------------------------------------
WIN:
    ./dita_deploy.sh -m DCScript.generateDeployScripts.win -p $PACKAGEID
---------------------------------------------------------------------
DCScript Deploy Corp:
---------------------------------------------------------------------
    ./dita_deploy.sh -m DCScript.deploy.corp -p $PACKAGEID
---------------------------------------------------------------------
DCScript Deploy AWC:
---------------------------------------------------------------------
    ./dita_deploy.sh -m DCScript.deploy.awc -p $PACKAGEID
---------------------------------------------------------------------
DCScript Deploy Dispatcher Win:
---------------------------------------------------------------------
    ./dita_deploy.sh -m DCScript.deploy.dispatcher.win -p $PACKAGEID
---------------------------------------------------------------------
DCScript Deploy Dispatcher Lnx:
---------------------------------------------------------------------
    ./dita_deploy.sh -m DCScript.deploy.dispatcher.lnx -p $PACKAGEID   
=====================================================================
Queries.customquery:
    ./dita_deploy.sh -m Queries.customquery -p $PACKAGEID
=====================================================================
Stylesheets.Import:
    ./dita_deploy.sh -m Stylesheets.Import -p $PACKAGEID
=====================================================================
Workflows.Import:
    ./dita_deploy.sh -m Workflows.Import -p $PACKAGEID
=====================================================================
AwcUiConfig.tilesDelete:
    ./dita_deploy.sh -m AwcUiConfig.tilesDelete -p $PACKAGEID
---------------------------------------------------------------------
AwcUiConfig.tilesAdd:
    ./dita_deploy.sh -m AwcUiConfig.tilesAdd -p $PACKAGEID
---------------------------------------------------------------------
AwcUiConfig.tilesUpdate:
    ./dita_deploy.sh -m AwcUiConfig.tilesUpdate -p $PACKAGEID
---------------------------------------------------------------------
AwcUiConfig.columnImport:
    ./dita_deploy.sh -m AwcUiConfig.columnImport -p $PACKAGEID
---------------------------------------------------------------------
AwcUiConfig.RelationBrowserDSImport:
    ./dita_deploy.sh -m AwcUiConfig.RelationBrowserDSImport -p $PACKAGEID
---------------------------------------------------------------------
AwcUiConfig.WorkspaceImport:
    ./dita_deploy.sh -m AwcUiConfig.WorkspaceImport -p $PACKAGEID
---------------------------------------------------------------------
AwcUiConfig:
    ./dita_deploy.sh -m AwcUiConfig -p $PACKAGEID
=====================================================================
NxAttributeMapping.Import:
    ./dita_deploy.sh -m NxAttributeMapping.Import -p $PACKAGEID
=====================================================================
ACL.Import:
    ./dita_deploy.sh -m ACL.Import -p  $PACKAGEID
=====================================================================
BatchLovs.Import:
    ./dita_deploy.sh -m BatchLovs.Import -p $PACKAGEID
=====================================================================
Classification.Import:
    ./dita_deploy.sh -m Classification.Import -p $PACKAGEID
=====================================================================
ClosureRules.Import:
    ./dita_deploy.sh -m ClosureRules.Import -p  $PACKAGEID
=====================================================================
CopyTcData.copyfiles:
    ./dita_deploy.sh -m CopyTcData.copyfiles -p  $PACKAGEID
=====================================================================
GenerateClientMetaCache.execute:
    ./dita_deploy.sh -m GenerateClientMetaCache.execute  -p  $PACKAGEID
=====================================================================
NXShare.copystartup:
    ./dita_deploy.sh -m NXShare.copystartup -p $PACKAGEID
---------------------------------------------------------------------
NXShare.copypvtrans:
    ./dita_deploy.sh -m NXShare.copypvtrans -p $PACKAGEID
---------------------------------------------------------------------
NXShare.copyapplication:
    ./dita_deploy.sh -m NXShare.copyapplication -p $PACKAGEID
---------------------------------------------------------------------
NXShare:
    ./dita_deploy.sh -m NXShare -p $PACKAGEID
=====================================================================
PostBMIDE:
    ./dita_deploy.sh -m PostBMIDE -p $PACKAGEID
=====================================================================
MetaDataCache 
    ./dita_deploy.sh -m MetaDataCache -p $PACKAGEID
---------------------------------------------------------------------
MetaDataCache.generateMetaDataCacheDelete
    ./dita_deploy.sh -m MetaDataCache.generateMetaDataCacheDelete -p $PACKAGEID
---------------------------------------------------------------------
MetaDataCache.clientMetaCacheDelete
    ./dita_deploy.sh -m MetaDataCache.clientMetaCacheDelete -p $PACKAGEID
---------------------------------------------------------------------
MetaDataCache.clientMetaCacheGenerate
    ./dita_deploy.sh -m MetaDataCache.clientMetaCacheGenerate -p $PACKAGEID
---------------------------------------------------------------------
MetaDataCache.generateMetaDataCache
    ./dita_deploy.sh -m MetaDataCache.generateMetaDataCache -p $PACKAGEID
=====================================================================
Backup
    ./dita_deploy.sh -m Backup -p $PACKAGEID
=====================================================================
Backup_MIG
    ./dita_deploy.sh -m Backup.mig -p $PACKAGEID
=====================================================================
Backup_NOSSO
    ./dita_deploy.sh -m Backup.nosso -p $PACKAGEID
=====================================================================
Backup_CORP
    ./dita_deploy.sh -m Backup.corp -p $PACKAGEID
=====================================================================
Backup.Preferences.Site
    ./dita_deploy.sh -m Backup.Preferences.Site -p $PACKAGEID
=====================================================================
Backup.tcdata
    ./dita_deploy.sh -m Backup.tcdata -p $PACKAGEID
=====================================================================
Backup.tcroot
    ./dita_deploy.sh -m Backup.tcroot -p $PACKAGEID
=====================================================================
Backup.volumes_dba
    ./dita_deploy.sh -m Backup.volumes_dba -p $PACKAGEID
=====================================================================
Backup.volumes_all
    ./dita_deploy.sh -m Backup.volumes_all -p $PACKAGEID
=====================================================================
Backup.dc.win
    ./dita_deploy.sh -m Backup.dc.win -p $PACKAGEID
=====================================================================
Backup.dc.lnx
    ./dita_deploy.sh -m Backup.dc.lnx -p $PACKAGEID
=====================================================================
Backup.deploymentcenter.win
    ./dita_deploy.sh -m Backup.deploymentcenter.win -p $PACKAGEID
=====================================================================
Backup.deploymentcenter.lnx
    ./dita_deploy.sh -m Backup.deploymentcenter.lnx -p $PACKAGEID
=====================================================================
Backup.dispatcherroot
    ./dita_deploy.sh -m Backup.dispatcherroot -p $PACKAGEID
=====================================================================
Backup.dispatcher
    ./dita_deploy.sh -m Backup.dispatcher -p $PACKAGEID
=====================================================================
Backup.awc
    ./dita_deploy.sh -m Backup.awc -p $PACKAGEID
=====================================================================
Backup.T4S
    ./dita_deploy.sh -m Backup.T4S -p $PACKAGEID
=====================================================================
Backup.SSO_WebTier
    ./dita_deploy.sh -m Backup.SSO_WebTier -p $PACKAGEID
=====================================================================
Backup.cpm
    ./dita_deploy.sh -m Backup.cpm -p $PACKAGEID
=====================================================================
Backup.db
    ./dita_deploy.sh -m Backup.db -p $PACKAGEID
=====================================================================
Backup.pooldb
    ./dita_deploy.sh -m Backup.pooldb -p $PACKAGEID
=====================================================================
SyncData.tc
    ./dita_deploy.sh -m SyncData.tc -p $PACKAGEID
=====================================================================
Dispatcher.deploy
    ./dita_deploy.sh -m Dispatcher.deploy -p $PACKAGEID
=====================================================================

Start Stop Scripts
=====================================================================
Start ALL
    ./dita_manage.sh -m startstopall -a start
---------------------------------------------------------------------
Stop ALL
    ./dita_manage.sh -m startstopall -a stop
=====================================================================


Service Status Lists
=====================================================================
    ./dita_manage.sh
---------------------------------------------------------------------
FSC
    ./dita_manage.sh -m FSC -a Status
    ./dita_manage.sh -m FSC -a Start
    ./dita_manage.sh -m FSC -a Stop
=====================================================================
POOL_IF
    ./dita_manage.sh -m Pool_IF -a Status
    ./dita_manage.sh -m Pool_IF -a Start
    ./dita_manage.sh -m Pool_IF -a Stop
=====================================================================
POOL_SSO
    ./dita_manage.sh -m POOL_SSO -a Status
    ./dita_manage.sh -m POOL_SSO -a Start
    ./dita_manage.sh -m POOL_SSO -a Stop
=====================================================================
SOLR
    ./dita_manage.sh -m SOLR -a Status
    ./dita_manage.sh -m SOLR -a Start
    ./dita_manage.sh -m SOLR -a Stop
=====================================================================
WEB_ALL
    ./dita_manage.sh -m WEB_ALL -a Status
    ./dita_manage.sh -m WEB_ALL -a Start
    ./dita_manage.sh -m WEB_ALL -a Stop
=====================================================================
WEB_IF
    ./dita_manage.sh -m WEB_IF -a Status
    ./dita_manage.sh -m WEB_IF -a Start
    ./dita_manage.sh -m WEB_IF -a Stop
=====================================================================
WEB_SSO
    ./dita_manage.sh -m WEB_SSO -a Status
    ./dita_manage.sh -m WEB_SSO -a Start
    ./dita_manage.sh -m WEB_SSO -a Stop
=====================================================================
WEB_IDSLOS
    ./dita_manage.sh -m WEB_IDSLOS -a Status
    ./dita_manage.sh -m WEB_IDSLOS -a Start
    ./dita_manage.sh -m WEB_IDSLOS -a Stop
=====================================================================
AWC_ALL
    ./dita_manage.sh -m AWC_ALL -a Status
    ./dita_manage.sh -m AWC_ALL -a Start
    ./dita_manage.sh -m AWC_ALL -a Stop
=====================================================================
AWC_MICRO
    ./dita_manage.sh -m AWC_MICRO -a Status
    ./dita_manage.sh -m AWC_MICRO -a Start
    ./dita_manage.sh -m AWC_MICRO -a Stop
=====================================================================
CPM
    ./dita_manage.sh -m CPM -a Status
    ./dita_manage.sh -m CPM -a Start
    ./dita_manage.sh -m CPM -a Stop
=====================================================================
TCIF
    ./dita_manage.sh -m TCIF -a Status
    ./dita_manage.sh -m TCIF -a Start
    ./dita_manage.sh -m TCIF -a Stop
=====================================================================
DC_ALL
    ./dita_manage.sh -m DC_ALL -a Status
    ./dita_manage.sh -m DC_ALL -a Start
    ./dita_manage.sh -m DC_ALL -a Stop
=====================================================================
DC
    ./dita_manage.sh -m DC -a Status
    ./dita_manage.sh -m DC -a Start
    ./dita_manage.sh -m DC -a Stop
=====================================================================
PUBLISHER
    ./dita_manage.sh -m PUBLISHER -a Status
    ./dita_manage.sh -m PUBLISHER -a Start
    ./dita_manage.sh -m PUBLISHER -a Stop
=====================================================================
REPO
    ./dita_manage.sh -m REPO -a Status
    ./dita_manage.sh -m REPO -a Start
    ./dita_manage.sh -m REPO -a Stop
=====================================================================