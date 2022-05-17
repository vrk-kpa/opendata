import {Stack} from "aws-cdk-lib";
import {Construct} from "constructs";

import * as bak from "aws-cdk-lib/aws-backup";
import {BackupStackProps} from "./backup-stack-props";

export class BackupStack extends Stack {
  readonly backupPlan: bak.BackupPlan

  constructor(scope: Construct, id: string, props: BackupStackProps) {
    super(scope, id, props);

    if (props.backups) {

      let backupVault = null;

      if (props.importVault){
        backupVault = bak.BackupVault.fromBackupVaultName(this, 'backupVault', `opendata-vault-${props.environment}`)
      }
      else{
        backupVault = new bak.BackupVault(this, 'backupVault', {
          backupVaultName: `opendata-vault-${props.environment}`,
        });
      }


      this.backupPlan = new bak.BackupPlan(this, 'backupPlan', {
        backupPlanName: `opendata-plan-${props.environment}`,
        backupVault: backupVault,
        backupPlanRules: [
          bak.BackupPlanRule.daily(),
          bak.BackupPlanRule.weekly(),
          bak.BackupPlanRule.monthly1Year()
        ],
      });
    }
  }
}

