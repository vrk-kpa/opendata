import {CommonStackProps} from "./common-stack-props";

export interface SendToZulipProps extends CommonStackProps {
  zulipApiUser: string,
  zulipApiUrl: string,
  zulipStream: string,
  zulipTopic: string
}

