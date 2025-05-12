import {aws_certificatemanager as acm, aws_route53 as route53, Stack} from "aws-cdk-lib";
import {Construct} from "constructs";
import {CertificateStackProps} from "./certificate-stack-props";

export class CertificateStack extends Stack {
  readonly certificate: acm.ICertificate;
  constructor(scope: Construct, id: string, props: CertificateStackProps) {
    super(scope, id, props);

    // TODO: Remove once we move to suomi.fi domain, cannot be updated without rebuilding few stacks
    const alternativeNamePrefixes: string[] = [
      "www",
      "vip"
    ]

    const alternativeNames: string[] = alternativeNamePrefixes.map((name) => {
      return name + "." + props.zone.zoneName
    })

    const secondaryAlternativeNames: string[] = alternativeNamePrefixes.map((name) => {
      return name + "." + props.alternativeZone.zoneName
    })

    secondaryAlternativeNames.push(props.alternativeZone.zoneName)

    const validationZones: {[key: string]:  route53.IHostedZone }= {
      "avoindata.fi": props.zone
    }
    alternativeNames.forEach((name) => {
      validationZones[name] = props.zone
    })

    secondaryAlternativeNames.forEach((name) => {
      validationZones[name] = props.alternativeZone
    })


    this.certificate = new acm.Certificate(this, 'Certificate', {
      domainName: props.zone.zoneName,
      subjectAlternativeNames: alternativeNames.concat(secondaryAlternativeNames),
      validation: acm.CertificateValidation.fromDnsMultiZone(validationZones)
    })
  }
}
