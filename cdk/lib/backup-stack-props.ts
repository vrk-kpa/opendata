import {CommonStackProps} from "./common-stack-props";

export interface BackupStackProps extends CommonStackProps {
    importVault: boolean;
    backups: boolean;

}
