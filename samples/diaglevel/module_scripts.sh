build_init()
{
    true
}

build_finish()
{
    true
}

build_template()
# SYSTEM_NAME - the name of the lennoxs30 system
{
   sed "s/SYSTEM_NAME/$1/g" lennoxs30_diag_level_template_package.yaml > $TARGET/packages/lennoxs30_diagmode_template_$1_package.yaml
   sed "s/SYSTEM_NAME/$1/g" lennoxs30_diag_level_template_automation.yaml > $TARGET/automation/lennoxs30_diagmode_template_$1_automation.yaml
}

