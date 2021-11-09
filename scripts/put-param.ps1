$prf = Read-Host "Profile"
$env = Read-Host "Environment"

while ($key -ne "exit")
{
    $key = Read-Host "Key"
    $val = Read-Host "Value"
    $path = "/$env/opendata/$key"

    aws-vault exec "$prf" -- aws ssm put-parameter --name "$path" --type "String" --value "$val"

    Write-Output "Set parameter $path to $val"
}