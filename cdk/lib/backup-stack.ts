import {Stack} from "aws-cdk-lib";
import {Construct} from "constructs";

import * as bak from "aws-cdk-lib/aws-backup";
import {BackupStackProps} from "./backup-stack-props";

export class BackupStack extends Stack {
  constructor(scope: Construct, id: string, props: BackupStackProps) {
    super(scope, id, props);

    if (props.backups) {
      new bak.BackupVault(this, 'backupVault', {
        backupVaultName: `opendata-vault-${props.environment}`,
      });
    }
  }
}

