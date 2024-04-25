import {EnvStackProps} from "./env-stack-props";

export interface BackupStackProps extends EnvStackProps {
    importVault: boolean;
    backups: boolean;

}
