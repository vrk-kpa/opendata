import {EnvStackProps} from "./env-stack-props";

export interface SendToZulipProps extends EnvStackProps {
  zulipApiUser: string,
  zulipApiUrl: string,
  zulipStream: string,
  zulipTopic: string
}

