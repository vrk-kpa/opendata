import {EnvStackProps} from "./env-stack-props";

export interface ShieldStackProps extends EnvStackProps{
  bannedIpsRequestSamplingEnabled: boolean,
  requestSampleAllTrafficEnabled: boolean,
  highPriorityRequestSamplingEnabled: boolean,
  rateLimitRequestSamplingEnabled: boolean
}
