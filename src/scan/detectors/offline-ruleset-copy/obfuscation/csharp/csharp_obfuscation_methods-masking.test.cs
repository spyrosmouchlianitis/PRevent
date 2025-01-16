// TP
Convert.ToString(Convert.ToString(Convert.ToString(123)));
string.Concat(string.Concat(string.Concat("a", "b"), "c"), "d");
"abc".Replace("a", "b").Replace("b", "c").Replace("c", "d");
new StringBuilder().Append("x").Append("y").Append("z");
char.ToUpper(char.ToUpper(char.ToUpper('a')));
Encoding.UTF8.GetBytes(Encoding.UTF8.GetBytes(Encoding.UTF8.GetBytes("test")));
Convert.ToInt32(Convert.ToInt32(Convert.ToInt32("123")));
BitConverter.ToString(BitConverter.ToString(BitConverter.ToString(new byte[] { 0x01 })));
Convert.FromBase64String(Convert.FromBase64String(Convert.FromBase64String("dGVzdA==")));
string.Join(",", string.Join(",", string.Join(",", new[] { "1", "2" })));
"abc".Substring(1).Substring(1).Substring(1);
new Random().Next().ToString(new Random().Next().ToString(new Random().Next().ToString()));
Encoding.ASCII.GetString(Encoding.ASCII.GetString(Encoding.ASCII.GetString(new byte[] { 65 })));
Guid.NewGuid().ToString(Guid.NewGuid().ToString(Guid.NewGuid().ToString()));
Path.Combine(Path.Combine(Path.Combine("a", "b"), "c"), "d");


// FP
Convert.ToString(123);
string.Concat("a", "b");
"abc".Replace("a", "b");
new StringBuilder().Append("x");
char.ToUpper('a');
Encoding.UTF8.GetBytes("test");
Convert.ToInt32("123");
BitConverter.ToString(new byte[] { 0x01 });
Convert.FromBase64String("dGVzdA==");
string.Join(",", new[] { "1", "2" });
"abc".Substring(1);
new Random().Next().ToString();
Encoding.ASCII.GetString(new byte[] { 65 });
Guid.NewGuid().ToString();
Path.Combine("a", "b");
HashAlgorithm.Create().ComputeHash(new byte[] { 0x01 });
