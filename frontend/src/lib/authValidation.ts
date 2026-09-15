export function emailError(value:string) {
  const email=value.trim();
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email) && !email.includes('..') ? '' : '请输入有效的邮箱地址';
}

export function passwordChecks(value:string) {
  return [
    {label:'至少 10 位',ok:value.length>=10},
    {label:'包含字母',ok:/[A-Za-z]/.test(value)},
    {label:'包含数字',ok:/\d/.test(value)},
    {label:'包含特殊字符',ok:/[^A-Za-z0-9\s]/.test(value)},
  ];
}
