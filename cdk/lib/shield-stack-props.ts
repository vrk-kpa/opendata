import {CommonStackProps} from "./common-stack-props";

export interface ShieldStackProps extends CommonStackProps{
  bannedIpsRequestSamplingEnabled: boolean,
  requestSampleAllTrafficEnabled: boolean,
  highPriorityRequestSamplingEnabled: boolean,
  rateLimitRequestSamplingEnabled: boolean
}
