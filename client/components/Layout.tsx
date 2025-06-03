import { SafeAreaView, View } from 'react-native';

const Layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <View className="flex-1 bg-slate-600">
      <SafeAreaView className="mx-4 flex-1">{children}</SafeAreaView>
    </View>
  );
};

export default Layout;
